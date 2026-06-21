# PolaUUH 线上注册登录三方快捷入口测试报告

日期：2026-06-21

## 覆盖范围

- 登录页第三方快捷入口展示。
- 注册页第三方快捷入口展示。
- `next` 参数在 provider start 链接中的保留。
- 未配置授权参数时 provider start 路由安全返回登录页。

## 测试命令

```bash
.venv/bin/python -m py_compile app/auth.py app/__init__.py
.venv/bin/python -m pytest tests/test_polauuh_provider_entrypoints.py -q
.venv/bin/python -m pytest tests/test_polauuh_auth.py tests/test_polauuh_provider_entrypoints.py -q
```

## 本地结果

- 编译检查：通过。
- 新增 provider 入口测试：3 passed。
- PolaUUH 账号兼容测试：5 passed。

## 线上验证

待部署后回填。
