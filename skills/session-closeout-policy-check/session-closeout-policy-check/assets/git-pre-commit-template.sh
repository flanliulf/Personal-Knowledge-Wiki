#!/bin/sh
# 将路径替换为已确认的绝对路径；只在获准安装后接入现有 pre-commit。
# 此模板仅核对报告与实际 index，不执行语义审查，不覆盖其他 Hooks。
exec "/ABS/PYTHON" -B "/ABS/SKILL/scripts/closeout_check.py" verify --request "/ABS/RUN/request.json"
