# lc-agent

The lc-agent context covers scheduled Agent work and the user-facing outcomes
created around that work.

## Automation Notifications

**Automation Task**:
A persisted schedule that asks one selected Agent to complete a defined piece
of work.
_Avoid_: Cron job, timer task

**Automation Run**:
One concrete execution of an Automation Task, regardless of whether it
succeeds, fails, or is skipped.
_Avoid_: Task, schedule

**Notification Target**:
A group destination configured directly on one Automation Task. It identifies
one messaging platform, one group name, and one group Webhook.
_Avoid_: Notification channel, subscription

**Notification Delivery**:
One attempt to send one Automation Run outcome to one Notification Target.
It has a delivery outcome independent from the Automation Run outcome and is
not retried automatically.
_Avoid_: Task status, notification status

**Delivery Summary**:
The aggregate notification outcome shown on an Automation Run when it has one
or more Notification Deliveries.
_Avoid_: Automation Run status, notification history
