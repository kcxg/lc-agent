"""把框架自带的「关联提示词」同步进业务库（prompt_templates 表）。

设计要点：
- 代码是唯一事实来源：展示名 / 正文改了，重启即覆盖数据库里的那一行
- 只按固定主键 upsert：不删除任何行（用户可能已经把它绑给了某个 Agent），
  也不自动绑定任何 Agent —— 绑定是用户自己在「Agents 管理 → 关联提示词」里做的选择
- 这些行的 source 固定为 "builtin"，接口层据此禁止改删
"""
from lc_agent.db.engine import get_async_session
from lc_agent.db.models import PromptTemplateDB, utcnow
from lc_agent.prompts.free_related_prompts import (
    builtin_prompt_db_id,
    prompts_added_to_db,
)
from lc_agent.utils.loggers import db_logger

BUILTIN_PROMPT_SOURCE = "builtin"


async def sync_builtin_prompts(db_url: str) -> int:
    """同步内置提示词，返回本次新增 / 更新的条数。"""
    changed = 0
    session = get_async_session(db_url)
    try:
        for prompt_cls in prompts_added_to_db:
            prompt_id = builtin_prompt_db_id(prompt_cls)
            row = await session.get(PromptTemplateDB, prompt_id)
            if row is None:
                session.add(
                    PromptTemplateDB(
                        id=prompt_id,
                        name=prompt_cls.name,
                        content=prompt_cls.prompt,
                        source=BUILTIN_PROMPT_SOURCE,
                    )
                )
                changed += 1
                continue
            if (row.name, row.content, row.source) != (
                prompt_cls.name,
                prompt_cls.prompt,
                BUILTIN_PROMPT_SOURCE,
            ):
                row.name = prompt_cls.name
                row.content = prompt_cls.prompt
                row.source = BUILTIN_PROMPT_SOURCE
                row.updated_at = utcnow()
                changed += 1
        if changed:
            await session.commit()
            db_logger.info("Synced %d builtin prompt(s)", changed)
    finally:
        await session.close()
    return changed
