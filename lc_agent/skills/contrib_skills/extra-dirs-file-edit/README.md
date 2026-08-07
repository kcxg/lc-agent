
# 说明：

这个extra-dirs-file-edit 的skill是给 traework 用的， traework 中无法跨项目编辑文件，需要powershell调用命令行，编辑失误风险高还每次都要审批，所以封装一个skill

lc-agent的项目模式，从源头就解决了这个问题，因为lc-aegnt的前端里面，可以设置额外允许操作的文件夹，lc-aegnt自身不需要这个skill。