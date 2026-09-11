# 本地插件更新与部署

源码更新和插件安装是两个步骤。以 Git 提交确定源码来源；开发阶段与正式发布可能使用相同版本号，不能仅凭 `1.3.0` 判断内容一致。

## 日常修改

1. 在正式本地仓库检查 `git status --short --branch` 和 `git remote -v`。保留未提交改动及独立提交。
2. 获取远端更新，使用 `git switch main` 和 `git merge --ff-only origin/main` 同步。出现分叉时先处理具体差异，不强制覆盖。
3. 从 main 创建开发分支，修改、运行与改动相关的测试，提交并推送，然后创建 PR。
4. PR 合并后同步本地 main。稳定部署选定正式 Tag；开发验证可以选择明确的提交，但应标注为开发构建。
5. 从选定源码构建并安装插件，在新任务中验证实际加载结果。

仓库远端统一为 `https://github.com/xianxianjianjian/Literature-Evaluation-Skills.git`。若存在单独的错误 push URL，使用 `git remote set-url --push origin` 修正为该地址。

## 构建

使用 Python 3.11、`requirements-exact-mirror.txt` 中的依赖及 Poppler。缺少依赖时使用项目专用虚拟环境。真实中文渲染还需要本机合法安装的 `C:\Windows\Fonts\simsun.ttc`。

在选定源码目录运行以下命令；将占位符替换为本次版本及提交短号：

```powershell
py -3.11 scripts/build_plugin_bundle.py --output dist/literature-evaluation-<version>-<commit>
py -3.11 scripts/validate_plugin_package.py --plugin-root dist/literature-evaluation-<version>-<commit>/plugins/literature-evaluation
```

构建脚本拒绝覆盖现有目录。保留旧构建并选择新的目录名，不删除目录来规避此保护。安装包只包含脚本规定的插件资源；研究数据、私人论文及字体文件不得加入包中。

在包目录旁记录源码提交、构建时间与命令。不要为记录部署信息而修改已发布 Tag 或其源码。

## 更新安装

使用当前客户端支持的插件管理入口。可用 CLI 时先查看 `codex plugin --help`、`codex plugin marketplace --help`；不要假设所有客户端的命令相同。

本机支持以下命令的客户端可使用：

```powershell
codex plugin marketplace list
codex plugin marketplace add <新构建目录的绝对路径> --json
codex plugin add literature-evaluation@literature-evaluation-local --json
```

如果 add 明确提示同名 marketplace 已绑定其他来源，先记录旧来源并保留旧包，再执行 `codex plugin marketplace remove literature-evaluation-local --json`，随后添加新目录并安装。该操作切换 marketplace 注册来源，不要求删除旧构建目录。若新来源添加失败，重新添加记录的旧来源恢复配置。

如客户端只能重新安装，使用其支持的卸载/安装入口。不要直接编辑插件缓存。安装成功后启动新任务，检查四个 `literature-evaluation:` 入口及其实际 Skill 路径。显示版本号、缓存目录存在和结构校验均不能单独代替新任务加载验收。

## 验证及交付

- 从更新后的包初始化独立临时工作区，执行 README 中的插件/工作区校验；现有科研数据目录保持不变。
- 复用现有 acceptance 和 workflow completion 测试验证检索、翻译、精读及总控状态路由，并明确区分静态检查、状态机测试和实际学术任务。
- 使用现有小型 exact-mirror fixture 与真实 SimSun 运行代表性渲染和独立验证；将合成或局部测试标明，不宣称为真实论文全文完成。
- 遇到测试失败，记录原始失败、原因和修复后结果。源码修复放在独立分支，不覆盖已发布 Tag。
- 若生成交付 DOCX，执行元数据清理并检查 `docProps/core.xml`。
- 交付远端/本地提交、构建来源、实际加载路径、Python 环境、测试范围及结果、旧包恢复方式。

部署未改变渲染逻辑时，不要求重复完整真实论文发布回归。涉及渲染、字体或版式行为变更时，依据受影响行为补充回归。

研究数据保存在独立 `.literature-evaluation` data root。升级、卸载或恢复插件时均不删除这些数据。恢复到旧插件时，重新注册已保留的旧 marketplace 并安装，然后开启新任务验证。
