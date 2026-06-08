# PRD: SkillHub and Job Guard - 2026-06-07

## User Story

作为 PolaZhenJing 管理员，我希望 SkillHub 和文章生成任务在服务器压力较大时仍能稳定工作，不因为频繁扫描、超大 zip 或线程爆发拖慢服务。

## Product Behavior

- SkillHub 列表仍支持搜索、分类、下载和管理员导入。
- 短时间内重复访问 SkillHub 使用缓存结果。
- 上传或导入过大的 zip 时显示失败提示。
- 超大的 skill 包下载返回 HTTP 413。
- 多个后台任务进入固定线程池排队执行。

## Compatibility

- URL 不变。
- 表单字段不变。
- job 状态表不变。

## Edge Cases

- registry 更新后立即清空缓存。
- GitHub zip 没有 Content-Length 时按读取累计字节数限制。
- zip 包路径穿越仍按原逻辑拒绝。
