# AL02 continuation release readiness

Read-only discrepancy inventory, 2026-11-10. Candidate HEAD `c87ea121510f82910885dbe4e62ed2ff1fea201a`, checkout `D:/OraLab/src/Ora2.0-director-qualification`. This inventory precedes any correction. Only this document changes; no commit. Runtime identity remains OPEN because installed raw snapshots are unavailable in the inspected evidence. This is useful engineering reconciliation, not a PARK recommendation or an installation/science authorization.

## Scope, provenance and authority

Inspection uses raw-byte SHA-256, JSON, AST/source inspection and local Git only. No production checkout, attempt path, installed interpreter/dependency readback, network, worker, custody, Job, claim or World was accessed or invoked. The sole permitted test is the exact_artifacts authority-absent test. Its existing imports are the explicit exception to static inspection; no other execution module was imported by inspection code. All three admission authorization constants were AST-checked as `None`.

The accepted [release package](AL02-CONTINUATION-RELEASE.md) and its engineering ACCEPT are preserved, not repeated. Frozen records govern historical commitments; they do not verify current installed bytes. Candidate raw working-tree bytes and local Git blobs govern candidate identity. Neither supersedes the other implicitly. No declaration, Git blob, log of a digest, or fixture receipt is treated as a raw installed-source snapshot.

Evidence roots: `A = D:/OraLab/reports/ora-al02-natural-b-panel-20261109`; `V = D:/OraLab/drafts/ora-al02-release-v3`; `R = D:/OraLab/drafts/ora-director-cross-objective/runs`. These preserved records were read without visiting their embedded production paths. Hashes below are exact raw SHA-256 unless explicitly labeled LF/Git or derived CRLF.

| Evidence provenance | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `A\contexts.json` | 41438 | `065149a3c3aa278c9dbc14527a8f54e354602e6ebcd3a87360cf20fa6e377804` |
| `A\campaign-binding.json` | 16588 | `c1711e6b33ad9784bf408cc92345998758ef9f4c590d680290aba30da5ef4e0b` |
| `A\campaign-package.json` | 214 | `50d0d3995e2b9358db4a79b02c6e00f439604012fdf55360c65012b05edef06b` |
| `A\continuation-binding.json` | 2205 | `a7f477b626a96a0d26f822473e88ebea585e1ce2d74d6596548cb2ff26fd1a5d` |
| `A\continuation-package.json` | 272 | `c9ffccf5dead5e6693b5fedfa3d2d42923e94d3ef44b0e221304140ce6500462` |
| `A\supervised-eight-binding.json` | 887 | `c12a44cd19ba01f5b84b4f2467835797b09c645a39b1209aeb1aa086a1e292c5` |
| `A\campaign-verification.json` | 1727 | `7a1efbd5ccd3403b3a904e382af4162a34812b31997c6f8d6c2d1a92156dc4a3` |
| `V\installed-binding-v3.json` | 20518 | `922f882c0d9013408f0c4a94c9c9c7643f8b844eb90dd3174aba3b7b409329d9` |
| `V\source-pins-v3.json` | 15266 | `b340270c30338a1f3e60d90baa82a732f5ffb7975faf7cbbb665f4775b552fdb` |
| `V\installation-verification-v3.json` | 1718 | `3ab4ba0d58a880c729f3f4b4725b2b1f3eeac627fb388fb1a418b0013ca4dbaf` |
| `V\human-release-package-v3.json` | 563 | `5888daa5741a4eeb070c5ab0e22ed584f98bd4158779f7ba7b125bd886025bcb` |
| `docs\AL02-CONTINUATION-RELEASE.md` | 16920 | `e41d1ec56dee21fd4763121f29adae3f583f88c5a0827bcaf0842f9f8773c07a` |
| `tests\test_al02_continuation.py` | 43970 | `5e2a4eb72cb0a57eebff15a8f3ceee6d8319755b7f35e34bf094b8b943c7389e` |
| `tools\build_al02_campaign.py` | 3071 | `667b1ff4639dbfaa40531ba471df74a49a6bbb5484c489d2cb722a03bff1c2cc` |

`tools/build_al02_campaign.py` statically verifies V/installed-binding-v3.json hash `922f882c0d9013408f0c4a94c9c9c7643f8b844eb90dd3174aba3b7b409329d9`, inherits its `installed_file_pins`, checkout and production HEAD, and replaces only one-pair, worker and custody pins with candidate bytes. This establishes the frozen producer pin provenance; the builder was not run. Continuation inherits campaign runtime pins through `continuation_binding()`; it adds no different executable inventory. Artifact-link hashes were read from JSON and checked against the raw files; the permitted test additionally checks the inactive exact artifacts.

## Complete frozen runtime inventory

Each source path below is relative to frozen checkout `D:\OraLab\src\Ora2.0-al02-first-depletion-20261109`; candidate comparisons use the same relative path under this worktree only. MATCH means candidate raw bytes equal the frozen declaration, never installed verification. Installed raw bytes are **unavailable for every row**: no corresponding preserved raw installed-source snapshot was found in the inspected A/V records or reviewed logs. Git sources and receipt declarations are available instead.

| Checkout-relative source | Frozen SHA-256 | Candidate raw SHA-256 | Comparison |
| --- | --- | --- | --- |
| `experiments/__init__.py` | `d1b4e4db64becb173467ca4fc66c8770e14411b895ea5305a8fe6d2d359a15ab` | `d1b4e4db64becb173467ca4fc66c8770e14411b895ea5305a8fe6d2d359a15ab` | MATCH |
| `experiments/al02_depletion_checkpoint.py` | `bf0ea2bb1ea20344815ae8a1e298d83b723852d370e0931cf4f52a2b01417606` | `bf0ea2bb1ea20344815ae8a1e298d83b723852d370e0931cf4f52a2b01417606` | MATCH |
| `experiments/al02_depletion_producer.py` | `266677b97c920a11359f818943c17aef240578b8cf58220c14d9d5333a1a0279` | `6d822b98540968fe94ef4a21624af91974d715537b582d869372cee78f55acc4` | MISMATCH P1 |
| `experiments/al02_depletion_projection.py` | `902c91ec39884e192037cdd8d73c9d7ff72db36cfffd5bf591bd2bc0b2432e62` | `902c91ec39884e192037cdd8d73c9d7ff72db36cfffd5bf591bd2bc0b2432e62` | MATCH |
| `experiments/al02_depletion_suffix.py` | `a8d0f372a6a4790adbd9f44f060adbb58abe7a910aacff3c7d780409da1eb4f6` | `a8d0f372a6a4790adbd9f44f060adbb58abe7a910aacff3c7d780409da1eb4f6` | MATCH |
| `experiments/al02_one_pair.py` | `f8c15c0338441d11877b4b9787fc33594a93a49394a5539dc4d4c3313f90e238` | `f8c15c0338441d11877b4b9787fc33594a93a49394a5539dc4d4c3313f90e238` | MATCH |
| `experiments/al02_one_pair_custody.py` | `28ffe0b56a3b0dbb43f7c9d78e46816952a9596787eeb355d2cb4fce01b48c4b` | `28ffe0b56a3b0dbb43f7c9d78e46816952a9596787eeb355d2cb4fce01b48c4b` | MATCH |
| `experiments/al02_one_pair_job.py` | `b4303bab60369dde319020a9bb18691999b977ad820fd9d535936bab509f2491` | `b4303bab60369dde319020a9bb18691999b977ad820fd9d535936bab509f2491` | MATCH |
| `experiments/al02_one_pair_worker.py` | `95607ddeefb232479f1ea5f8b8aa695cf343e558367aa30dfe62fa900cec25f1` | `95607ddeefb232479f1ea5f8b8aa695cf343e558367aa30dfe62fa900cec25f1` | MATCH |
| `experiments/al02_selection_referee.py` | `c4b080f9ec25814054407c862730d3fbd1627d7f8d23dcfdce456213a3ca8cbc` | `c4b080f9ec25814054407c862730d3fbd1627d7f8d23dcfdce456213a3ca8cbc` | MATCH |
| `experiments/al02_selection_request.py` | `4568d4cdeb5f8d8385602d420a3e4c0783d2b44356a8d4475253e43a824b87eb` | `4568d4cdeb5f8d8385602d420a3e4c0783d2b44356a8d4475253e43a824b87eb` | MATCH |
| `experiments/causal_genealogy_audit.py` | `18391a36b871e3a2a7d18c01a3a5b1520ae92f4e36a0c967e11ca1ef5c25e12c` | `18391a36b871e3a2a7d18c01a3a5b1520ae92f4e36a0c967e11ca1ef5c25e12c` | MATCH |
| `experiments/executed_heredity.py` | `03e3f1035233e8e1a078cd401ee10857de8ea20dc0249dd6c973675e8fc80342` | `03e3f1035233e8e1a078cd401ee10857de8ea20dc0249dd6c973675e8fc80342` | MATCH |
| `experiments/process_limits.py` | `5b6f3df66078955c772ab99f2ac20d79826005dd88f152a2201a7017a53f5776` | `5b6f3df66078955c772ab99f2ac20d79826005dd88f152a2201a7017a53f5776` | MATCH |

14 checkout-relative pins: 13 matches and one producer discrepancy. The remaining 83 pins are interpreter/runtime files. Full absolute path and frozen hash follow; candidate/installed readback is UNAVAILABLE for each. None was opened or dynamically imported for this inventory. No inferred match from the test interpreter is counted. These files are inherited unchanged from V/installed-binding-v3.json; compare their declarations using the reproduction script.

| Absolute runtime path | Frozen SHA-256 | Candidate / installed bytes |
| --- | --- | --- |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\DLLs\_bz2.pyd` | `8eecdcc250637652e6babc306ea6b8820e9e835ddd2434816d0e0fd0ca67fd14` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\DLLs\_ctypes.pyd` | `af598ae52ddc6869f24d36a483b77988385a5bbbf4618b2e2630d89d10a107ee` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\DLLs\_hashlib.pyd` | `441d32922122e59f75a728cc818f8e50613866a6c3dec627098e6cc6c53624e2` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\DLLs\_lzma.pyd` | `33ae42f744d2688bb7d5519f32ff7b7489b96f4eea47f66d2009dba6a0023903` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\__future__.py` | `bf11d13b6c9b2b8706be425addf399965738622bb4cc553217be16399c51d51a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\_collections_abc.py` | `07653c161374fb79c8f6d2688cf3ae1b6a6e5f4c973fb3d39329b6fdd83cf43f` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\_compression.py` | `a10cf1a317374641bcdb8252499e9cb9d4d6e774ac724edfdddd0433ead771d9` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\_weakrefset.py` | `cf8031a6e21150438f3d2964c4152615b91a03894616d5b6930e0f14f44dabda` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\abc.py` | `c01ba83c5602d006efbf5868d53075cb6997aa069b4b6c6e2c6155cb282d9e0a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\argparse.py` | `6d4d699ab5b717c4b2b51414f8b94a61f7c3c1900df9cf19c92e60bb2a5e5e85` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\ast.py` | `3f1e53ddcfd58b075938646cf51e98e624f2b6721abc1d9d24ddf34500784328` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\bisect.py` | `05d6b239ee3d6114a682aa9a5efb8f8b315cce6fc2a5d6f1147192ab5a044f44` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\bz2.py` | `a539fc503737c53d5a45272e33a435b8a6b7a8559ba6a425002978038096bd66` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\codecs.py` | `4635485d9d964c57317126894adaca91a027e017aefd8021797b05415e43dbb4` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\collections\__init__.py` | `f0067232ba9d4e8f7186e7c9c78aea16cc78494089d299e91dbd1f55f54161de` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\collections\abc.py` | `7ad86878712fc6682863f12208f4ced5daf2dd82b6ff5ed58207de29d0efa410` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\contextlib.py` | `afc1635de4b3a8e842735928e26ff444106df01c807d0f914744fd97bd8b6a5f` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\copy.py` | `82afa1d570d4d328efbba5cde3fc21025a44e3cfe5e10d9316a73745194a236b` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\copyreg.py` | `a04efa4d0f7034a190700f4df14893f09b37bc51e8ad6ed441fa9200a7f0bd52` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\ctypes\__init__.py` | `2b18d99447e66fb16d59c5d29da3bc221023d7da347e19886a55f8dfb3baefd3` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\ctypes\_endian.py` | `acdbc1c1de19616c735e0d9aa04ab0661fb4aaf4ead762c5a425cf809acb16eb` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\ctypes\wintypes.py` | `f0ebc6bb351c64eadec46014490c951a21798226bfbd487623c8630dcc0a21d8` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\dataclasses.py` | `011d2c5e9bcb6a1b4374cd771663514bee3b65f9729f333df94e0d6a1fc6147c` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\dis.py` | `efdfb83a9351ce4d381c9b9692247c9b69ee090a383d633e025cde6d0a039d7e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\encodings\__init__.py` | `8b997e9f7beef09de01c34ac34191866d3ab25e17164e08f411940b070bc3e74` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\encodings\aliases.py` | `1893cfb597bc5eafd38ef03ac85d8874620112514eb42660408811929cc0d6f8` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py` | `7acb7b80c29d9ffda0fe79540509439537216df3a259973d54e1fb23c34e7519` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\encodings\utf_8.py` | `9c54c7db8ce0722ca4ddb5f45d4e170357e37991afb3fcdc091721bf6c09257e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\enum.py` | `5d24be1ea17a4ed6169aa8c2c6155e1b3a9d2e7dd05a33332f855115f0e94190` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\fnmatch.py` | `146d27a2853cd14c95ee49cc6130b9f84e2a56618dd1be695cddb20489460425` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\functools.py` | `4c54da1d6c7adc78e975315929d6dc8d1262c189d8eec81e2fd70335bcb6ddb3` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\genericpath.py` | `2e162781cd02127606f3f221fcaa19c183672d1d3e20fdb83fe9950ab5024244` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\gettext.py` | `1f8e2b9940a7174cb2398b3633ba109eff123b148e01ffc9820c2c6421021054` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\hashlib.py` | `158b8e4d4f5fcecef24b840af0bee5632b27f948c74faf0810cc598b508e4f97` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\__init__.py` | `6d4ab4726790393388b483a56966276861eb3353731646572774ffa90b68289e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\_abc.py` | `c4376232da9464a27b02a530473489486d570f25a063715f3ad5a24d92ffe527` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\_bootstrap.py` | `cde7b67fb2bdd7012354840396d85e8ee18ea31966eb530666199701bc27c31b` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\_bootstrap_external.py` | `6062b44ee7caca7d17b68a5b1611d001173e9f5c30fb3c0805241c00d7dbedda` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\abc.py` | `7f7fa987e88c958e465b5ab1cb135f0fc85e21d2011bf3c8f41724a0711929f0` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\machinery.py` | `9a2ee437c38e45cdf7559f613f57209b5b11c0824a9069192b9ebd5a2ceefa1a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\resources\__init__.py` | `09ff374bdf81082cc52ea40c0f6ed172342bd6533a0196e4642cce52b9852ff1` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\resources\_adapters.py` | `aabea84ad2b7433ed0af7cda06503d7a901e87d7d4da5932b1c1917c1255e07a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\resources\_common.py` | `9af0425f10c688c05722e596a239ad3b1fc279ee3312473d3380d072c763179a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\resources\_legacy.py` | `e6e09fc9ab0dacf0450f520567617316ff23a691aedbf4e2228bdf11e3505847` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\resources\abc.py` | `1fc4889071fcd0d009d68b2f49289d0e82afac674586e5e810b6415584b602f4` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\importlib\util.py` | `b9a599e9047040ec13892bf784be3c733e5a2d8eff39331ef66cfbadd6b169cd` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\inspect.py` | `c4f44ca133d26697542e3a2fd8da3fd6b4fcd7634823ceb1541b4eed5830578a` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\io.py` | `8e902d070a3fe95d93596ea523ee4e691366b8cc6691c93a9276cc89c124cf61` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\json\__init__.py` | `feb17670e443e5db2723f217727dcc5d5e155c40e4e6935b16061c88542f24e7` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\json\decoder.py` | `b719fbcfcebd2b174f076e71292e22b1a17d9e258dbe896c768325383bad4f80` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\json\encoder.py` | `366a611e210eab51067773e1012b692a9b5c90dc5695bedbeb3a3fccec039e39` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\json\scanner.py` | `9841566fb17315ebdd40a1ca9cb214f02cde7171b187d4dc821c80120ea853c3` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\keyword.py` | `ebd724ed7e01ce97ecb3a6b296001fa4395bb48161658468855b43cff0e6eebb` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\linecache.py` | `9ed3ba77f235c8fcc60d00bd6b9aa9495c717b59c8ac9efb7c6ffdfe9b82b034` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\lzma.py` | `da46fa7c6c554a0705cf9a7318279b56fd5f62f71a55ac28e9579616f11129d6` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\ntpath.py` | `ea012f56af4f542c323cf060b231563c45c0610541a664ebcda16501cee6c793` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\opcode.py` | `8fcc88940c6d09bc323ece96b5cb4120c5ca00635825ef5ac84282157f9e577e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\operator.py` | `c57b6816cfddfa6e4a126583fca0a2563234018daec2cfb9b5142d855546955c` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\os.py` | `cca645ae16490e7426f7497905e6746c2c6a8d36cb2c04d85fc44b6ccea0198d` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\pathlib.py` | `c7543376b6cbab9886689d710994dcde66733f5d3a4b5711c90dc12c6c2c5801` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\platform.py` | `20298de350fa159b8cc9d4a045b974fd0dda978078b357eafb507b6e70b13e37` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\posixpath.py` | `232026ad59cecc9c4c05a0e23016da16a7c0c7660a6e46191806a757e419fd7f` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\random.py` | `7f5801a3045d0ca37044e6a346c4848263ad6a8d8a95a1129c61ce5fc397771d` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\re\__init__.py` | `e912249b8b1e2880ff212ef728e8becba893ce31bcb68aa2bfbcab2c812e61be` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\re\_casefix.py` | `a1a8ce5d2051c96abb0c854f4a9c513c219e821f7285d28330f84eca71c341e2` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\re\_compiler.py` | `712bb32f1d9d71e4f08486e5336c1303d65200d3249b1f6e0bef770f68164bbd` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\re\_constants.py` | `581e6c50e7f71e73f909567a4f2a06bed6b0f95098fdb60a18b8e3d39aa5b5e8` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\re\_parser.py` | `43c6a6d0873cfbbb1d76a74e72a5f7f6c8d0b09c4e9f427b27288d02d130384d` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\reprlib.py` | `e66e66eae80b0300b332df07949520bc59c8193f38b6fb848957c02985f3659b` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\shutil.py` | `2a6b6cfcf64df6a423cfe9d5c568e28eb8e1df03eb802418e131d96c952f0277` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\stat.py` | `e514fd41e2933dd1f06be315fb42a62e67b33d04571435a4815a18f490e0f6ce` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\struct.py` | `eadbcc540c3b6496e52449e712eca3694e31e1d935af0f1e26cff0e3cc370945` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\tempfile.py` | `130f717f7787a52064572f3138ef204f2be65773b831c947b4960b84359480b6` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\token.py` | `deef9e816f02d761501bb6e28870b204e2341d39d3d5d0131f5853781cbf2c0e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\tokenize.py` | `7c723db5c8f22bf930658bc89b2fab77f2d5702f3fefc116597f23051d028b7e` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\types.py` | `c762d2321a143aa9a7eaeb30f8ed8042c10a3e98e4fa678e4f659e2136bf85b5` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\typing.py` | `921e4d2397c8cb34394a7bf2532250088cdf8a48fec50cd64350c1f5f5186e07` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\urllib\__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\urllib\parse.py` | `87732780c13533bebbba2ba3b2045e1b724747e544740f7ecb1f66be3bee7569` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\warnings.py` | `dd8d3b7cead8aa956c330be2ac6f615409c2f42cee7c3ec5968989b624048f38` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\weakref.py` | `6721c34ba3c404bf4a443890ed374b546a870c958935a6aa4fdf634876a5a980` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\Lib\zipimport.py` | `a29b21fe4931e1833be162a68921ff35b5ec858a87bca94d95e7f44165bcf519` | unavailable / unavailable |
| `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\python.exe` | `0cbf71efa09ec4ce62d95c1448553314728ed5850720c8ad40352bfbb39be99a` | unavailable / unavailable |

## Discrepancies and smallest isolated corrections

### P1: producer raw identity is unresolved

`experiments/al02_depletion_producer.py`: frozen `266677b97c920a11359f818943c17aef240578b8cf58220c14d9d5333a1a0279`; candidate 5,170 bytes, `6d822b98540968fe94ef4a21624af91974d715537b582d869372cee78f55acc4`. V/installation-verification-v3.json records replacement before `ae47e3b3121fdc477f8144acf8817d5b47bcbddc05890d112d8f9c43402254cd` and after the frozen `266677...` value. V/installed-binding-v3.json separately names producer Git blob `10df7acd0ca2a09b8f8b10e98f3b56f6d08d9c66`. Local `git cat-file blob` of that blob equals the candidate after LF normalization (5,067 bytes; SHA-256 `c8ff0fc05cd49cd6bb89c43830cc4cb671701c9d13c66489f758f6daeab8414e`). Its derived CRLF serialization equals candidate raw bytes, not the frozen pin.

Local history `9d10445d64b927c6f6f65c86f48ca6bebf4195fc` changes `vars(obj).update(config, state['counters'])` into two calls, `update(config)` then `update(state['counters'])`. Frozen HEAD producer Git bytes (also `9d10445^`) are 5,042 LF bytes, SHA-256 `be0ad81cb5d70ae9ef0e390702a47f5543ae41bc4ac1184e9fc087d396bbe1ee`; derived CRLF SHA-256 is the replacement record's BEFORE value `ae47e3...`. Candidate equals the corrected Git version. This establishes the historical code correction and before-record linkage; it does **not** establish why the recorded AFTER raw hash differs from candidate. Neither LF nor CRLF serialization of the named corrected blob explains `266677...`; no raw installed snapshot was available to inspect. Do not call this a proven newline-only difference or assume the frozen pin is erroneous.

Historical authority: preserved V replacement/binding and A frozen binding for what was recorded; candidate authority: raw bytes and Git blob above. Smallest next correction: first obtain a preserved, independently authenticated raw installed producer snapshot under an allowed evidence-only scope, compare exact bytes and AST against the named blob, then review a separate successor runtime identity if needed. Do not overwrite the frozen binding, substitute a fresh digest, install a guessed version, or revert the reviewed correction. Remaining blockers: raw installed bytes, exact cause, intended successor identity and independent review.

### V1: six external verification entries describe earlier source

A/campaign-verification.json has 12 source entries: six match current raw bytes and six differ below. The table is freshly calculated, not copied from the accepted package. All twelve appear in the reproduction output. The record still links the same frozen campaign binding/package and declares `scientific_authorization: false`; its own trust field says independent reviewer publication identity must be provisioned before activation.

| Source | Historical recorded raw SHA-256 | Candidate raw SHA-256 | Local changes after initial campaign |
| --- | --- | --- | --- |
| `experiments/al02_campaign_admission.py` | `07b292f2a921b353d8dfe866442b024ebef8d73de307ddcd15c153c21b35a84c` | `536ec33a2a2901e5dc226ad8146781caf6a4a45921867897988b9e90acf9cd98` | 8ee2af0 pilot; 9b975cf STOP review; 7168db4 continuation |
| `tests/al02_release_rehearsal/campaign-controller-probe.py` | `861de732a41e2d91130397c2ba55a875e816f9113234d30c7846c225b30838fd` | `ed74674841d43a1560f39676f98ed99c74439d9434ddca4785c1627a39ad4c8a` | 8ee2af0 pilot; 9b975cf STOP review after 52f332b |
| `tests/test_al02_campaign_controller.py` | `088e5fd9aac5a486e3270cbf4086d4e1cf3df5b0bd3d2f0d8ff2a06a0eb10b8b` | `5a4600dd4858c2fa3a36c2f9ec1378104a64cd4b2216b9b67e20b3cd3fdb8aae` | 52f332b controller qualification; 8ee2af0 pilot |
| `tools/al02_campaign_evidence.py` | `bc26aadc799bd1b651ada0a53870bdb54918ecd541e3b34a43289e18ed2692c8` | `e476e23391badf5b4a0f314eedc802c79fab2384eb733aab56c1599089d4df6f` | 7168db4 continuation identity checks after 52f332b |
| `tools/al02_natural_b_analysis.py` | `da866be13e2f5435250cbf3749f9b561a74be3409108b3fc5d3519ee8c1a26df` | `46676791d672e1498b532e527e303615308bda4bfacbd2ab8fe92c8d312204eb` | No later Git content change; recorded raw serialization unresolved |
| `tools/run_al02_campaign.py` | `3a8a742bb957f4c2ca022b45960861ff1e8c487e7849b2434a69d857dac89b1e` | `f9addf68adc68933b72484c34189f08125f335282332010f896dd64dc5e8eee8` | 52f332b controller; 8ee2af0 pilot; 9b975cf STOP; 7168db4 continuation; dfd56d4 resources; f2fbf1b final review |

Cause is established only in part: the immutable verification record does not describe current raw candidate bytes. Four recorded hashes (probe, controller test, evidence join and runner) match LF or derived CRLF bytes at `52f332b265e5438b0370b080840976e09a95fb3a`; later Git changes explain source drift for these four. The admission and natural-analysis recorded hashes do not match any file-changing revision in the local `git log --all` search under LF or derived CRLF serialization. Natural analysis has no Git content change since its introduction `fbd3886`; its raw mismatch may reflect serialization or an uncommitted historical candidate, but neither cause is established without the old raw snapshot. Admission has later feature changes, but its exact old raw identity also remains unresolved. Git history does not prove that the earlier record was ever installed or that any later source was independently published as approved. Raw historical hash-to-Git matches can be reproduced below; absence of a match must remain uncertainty. Historical authority is the external record for its own recorded candidate only; current HEAD/raw bytes identify this candidate. Smallest isolated correction: review the changed source closure and publish a separate successor verification record tied to explicit candidate revision, paths, all runtime/artifact digests and trusted reviewer identity; retain the existing record. No correction is performed here. Blockers: candidate selection, producer resolution, full installed evidence, reviewer trust and independent approval.

### A1: admission is currently matching, not a new discrepancy

- `experiments/al02_campaign_admission.py` raw SHA-256 `536ec33a2a2901e5dc226ad8146781caf6a4a45921867897988b9e90acf9cd98`.
- `tools/run_al02_campaign.py` raw SHA-256 `f9addf68adc68933b72484c34189f08125f335282332010f896dd64dc5e8eee8`.

AST extraction of runner `ADMISSION_SHA256` equals candidate admission raw hash `536ec33a2a2901e5dc226ad8146781caf6a4a45921867897988b9e90acf9cd98`. The old verification entry `07b292...` is V1 staleness, not evidence that this matching runner pin should change. Preserve both current bytes and constant. Installed admission remains unavailable; no production readback is claimed.

### G1: checkout/revision and command identities are distinct

Frozen checkout `D:\OraLab\src\Ora2.0-al02-first-depletion-20261109`; frozen HEAD `485a46c1b3a2b26170f15ae415783f93d7cab753`. Candidate checkout `D:\OraLab\src\Ora2.0-director-qualification`; HEAD `c87ea121510f82910885dbe4e62ed2ff1fea201a`. `git show` inspects the frozen revision locally without opening its checkout. Frozen HEAD predates the producer correction; V explicitly records `pre_install_source_revision` `630b1515a03a8d0b10eb0d081ca17c631ad32530` and producer blob from the later source. A HEAD declaration alone therefore cannot identify the overlay bytes.

The controller statically requires both `Path(gate.__file__) == checkout/experiments/al02_campaign_admission.py` with matching raw pin and `git -C checkout rev-parse HEAD == production_head`. This worktree is a reviewed candidate, not the frozen installation. No controller was invoked to probe that mismatch. Historical authority: A/V declarations and local historical Git objects. Candidate authority: this checkout and HEAD. Smallest isolated correction: choose an explicit successor release revision/path plus byte inventory and review its overlay policy; preserve the historical HEAD/path in old records. Blockers: actual installed checkout/module identity and installed Git revision are unavailable, intended installation mapping unselected, installation unauthorized.

Exact proposed campaign argv is the following JSON template. `<index>` is a zero-padded committed index 008 through 127; only the placeholder varies. Windows separators and list-element boundaries matter. No shell expansion or implicit extra flag is part of this command.

```json
[
  "C:\\Users\\Jerem\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
  "-I",
  "-S",
  "-B",
  "D:\\OraLab\\src\\Ora2.0-al02-first-depletion-20261109\\experiments\\al02_one_pair_worker.py",
  "D:\\OraLab\\reports\\al02-natural-b-campaign-attempts-20261109\\attempt-<index>\\00-pending.json",
  "AL02-NATURAL-B-PANEL-20261109-v1"
]
```

CWD is exactly `D:\OraLab\src\Ora2.0-al02-first-depletion-20261109`. Admission owner is `hennessydesktop\hennessy`. AST/source at `al02_campaign_admission.admitted` and `run_al02_campaign.run_next` agrees on this command, token and pending path; continuation changes context selection/budget, not the worker or interpreter. The frozen interpreter `C:\Users\Jerem\AppData\Local\Programs\Python\Python311\python.exe` has declared pin `0cbf71efa09ec4ce62d95c1448553314728ed5850720c8ad40352bfbb39be99a`. Actual launch argv, interpreter bytes/version, owner, installed module file and dependency bytes are unavailable. A test launched with `python` does not verify that frozen installation.

V/proposed_command is a different historical successor invocation: same interpreter/flags/worker but pending under `al02-first-depletion-successor-20261109/attempt-v3` and token `AL02-SUCCESSOR-20261109-v3`. It is not a campaign admission receipt. Smallest correction is a separate exact launch/admission record for the chosen successor, with independently retained command and terminal pins; do not rewrite historical receipts. Missing installed launch evidence remains a blocker.

### S1: simulator/referee matches are bounded candidate evidence

Source inspection identifies simulator `experiments.executed_heredity` (`frozen.World`) and producer `EscrowContinuation`; one-pair driver calls the suffix verifier. Candidate campaign evidence names referee `experiments.al02_one_pair.verify_context`, while V historical referee text names `experiments.al02_one_pair.verify -> experiments.al02_depletion_suffix.verify_pair`. Those are different scope entries, not a demonstrated referee byte mismatch. Simulator, one-pair referee, suffix, selection referee, checkpoint and projection raw pins match the candidate in the complete table. Worker ProjectLoader checks exact source bytes and restricts the project module closure; the producer discrepancy remains within that required closure. No simulator or referee was executed.

Historical authority is V for the successor entry and A for the campaign commitment; candidate source establishes the current campaign entry. Smallest isolated correction: explicitly bind the selected campaign referee entry and raw source closure in a successor record and independently compare retained installed bytes. Preserve matching code. Blockers: installed simulator/referee and exact entry provenance, producer resolution, independently retained admission identities. A source match cannot certify scientific outcomes.

## Prior raw review evidence and preserved acceptance

Inspected R JSONL records as data. Relevant preserved raw logs/receipts are hashed below. The prior release reviewer explicitly returned ACCEPT for the documentation-only package at `47becb034b4925cd7be2d7e4a4fee35722b13f29`, with no activation/scientific authority. The accepted fixture reviewer returned ACCEPT on the retained inert evidence. These findings remain historical; they do not close runtime identity. The logs contain digests and source/test review, but no authenticated raw installed producer payload was identified.

| Preserved evidence | Raw SHA-256 |
| --- | --- |
| `R/76a68046-7ff4-420a-8c4e-a04e342a36ad.jsonl` | `a9f6b3e48a09719c98e56cd9f835f17a497406e96ac9d5ef024cbb3ddcbb8f11` |
| `R/178cfd89-fe40-4462-9275-ed447ccbf942.jsonl` | `7be9d9c4c48c25e151170dd398885081013c29cd9b7878d98233c8bc37da5fbc` |
| `R/c3f39849-29de-4061-92b1-7f4ccdea6e8b.jsonl` | `6ee3a5acf8b470491a3dd0caf39d1a71576f139d5b56a7fc0deb90b8d9f7a3a5` |
| `R/5cde20b4-5061-421b-99fd-6cad23b5d5c6.jsonl` | `67e1ff4851daa5d4773d83f64ffeeba63484690029293c387a88973c530ee323` |
| `R/c3f39849-29de-4061-92b1-7f4ccdea6e8b.receipt.json` | `b2eeb04940ac92aee102004d37238104e61dae7819bfabc8d98538fc3eae51f9` |
| `R/5cde20b4-5061-421b-99fd-6cad23b5d5c6.receipt.json` | `70b1aeb90201a6d9f8deb22bb2d3d240e3689653129e82cb13ccd8a848e15a02` |

The historical accepted 2-targeted/10-continuation results and all accepted tests/safeguards remain preserved; they were not rerun. The pre-task status was clean. No rejection of this inventory has been received.

## Reproduce without production access

From this candidate checkout, use the following standard-library-only inspection through `python -B -`. It never imports project modules, executes source, runs builders or dereferences frozen production/runtime paths. Do not replace the candidate path mapping with reads of frozen absolute paths. SHA-256 is over raw bytes; derived CRLF values are labeled separately. Follow with local `git show 9d10445 -- experiments/al02_depletion_producer.py` and `git log --oneline -- <source>` for each differing entry.

```python
from pathlib import Path, PureWindowsPath
import ast, hashlib, json, subprocess
H = lambda raw: hashlib.sha256(raw).hexdigest()
A = Path('D:/OraLab/reports/ora-al02-natural-b-panel-20261109')
V = Path('D:/OraLab/drafts/ora-al02-release-v3')
B = json.loads((A/'campaign-binding.json').read_bytes())
old = json.loads((V/'installed-binding-v3.json').read_bytes())
for root in (A, V):
    for p in sorted(root.glob('*.json')):
        print('RECORD', p, len(p.read_bytes()), H(p.read_bytes()))
for absolute, expected in B['pins'].items():
    assert old['installed_file_pins'].get(absolute) == expected or \
        PureWindowsPath(absolute).name in (
            'al02_one_pair.py', 'al02_one_pair_worker.py', 'al02_one_pair_custody.py')
    try:
        rel = PureWindowsPath(absolute).relative_to(
            PureWindowsPath(B['checkout'])).as_posix()
    except ValueError:
        print('UNAVAILABLE', absolute, expected)
        continue
    actual = H(Path(rel).read_bytes())
    print('SOURCE', rel, expected, actual, actual == expected)
E = json.loads((A/'campaign-verification.json').read_bytes())
for rel, expected in E['raw_source_sha256'].items():
    actual = H(Path(rel).read_bytes())
    print('EXTERNAL', rel, expected, actual, actual == expected)
    # Identify older declared hashes in local history, never in production.
    hits = []
    revs = subprocess.check_output(
        ['git','log','--all','--format=%H','--',rel], text=True).splitlines()
    for rev in revs:
        raw = subprocess.check_output(['git','show',rev+':'+rel])
        if expected in (H(raw), H(raw.replace(b'\n', b'\r\n'))):
            hits.append(rev)
    print('HISTORICAL_GIT_OR_DERIVED_CRLF_MATCHES', hits)
for rel, names in [
    ('tools/run_al02_campaign.py', ['ADMISSION_SHA256']),
    ('experiments/al02_campaign_admission.py', ['AUTHORIZATION_SHA256',
        'PILOT_AUTHORIZATION_SHA256','CONTINUATION_AUTHORIZATION_SHA256'])]:
    tree = ast.parse(Path(rel).read_bytes())
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for target in n.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    print('CONSTANT', rel, target.id, ast.literal_eval(n.value))
rel = 'experiments/al02_depletion_producer.py'
for rev in [B['production_head'], '9d10445', 'HEAD']:
    raw = subprocess.check_output(['git','show',rev+':'+rel])
    print('GIT_LF',rev,len(raw),H(raw))
    print('DERIVED_CRLF',rev,H(raw.replace(b'\n',b'\r\n')))
blob = subprocess.check_output(['git','cat-file','blob',old['project_git_blobs'][rel]])
assert blob == Path(rel).read_bytes().replace(b'\r\n',b'\n')
print('PRODUCER_RECORDED_BLOB_MATCHES_CANDIDATE_LF',H(blob))
```

Only permitted test: `python -B -m unittest discover -s tests -p test_al02_continuation.py -k exact_artifacts`. Result: PASS, exit 0; 1 test in 0.001 seconds, OK. The documented static reproduction script also completed successfully. `git diff --check` passed (Git reported only its normal LF-to-CRLF working-copy notice); final status contains only this document. HEAD remains the specified candidate. No accepted qualification was repeated.

## Remaining gates and authorized engineering

Engineering may continue as evidence-only review of preserved snapshots, local Git and candidate identities, clarification of the producer serialization/overlay discrepancy, and drafting a separate successor inventory for independent review. This task authorizes only this document; source/pin fixes need a new scoped task. Missing science authorization does not prevent this useful engineering work. Missing installed evidence keeps the runtime-identity criterion open; it does not justify PARK or manufacture a verified installation.

Installation/activation and scientific dispatch remain separately unauthorized. Before any future release: resolve P1; independently review V1 successor identity and reviewer trust; obtain installed raw source/runtime/interpreter, owner, exact argv/CWD/module and revision evidence; reconcile the historical overlay; verify unused claims, capacity, retained admissions and original terminal pins, each eight-context review and final review under an authorized scope. No attempts, receipts, frozen artifacts or accepted package may be rewritten to make declarations appear verified. Campaign/pilot/continuation authority remains None. No scientific outcomes are inferred from inert qualification.

Rollback if rejected: restore only this file from the pre-task HEAD blob `c87ea121510f82910885dbe4e62ed2ff1fea201a:docs/AL02-CONTINUATION-READINESS.md` (heading and original newline). Preserve review evidence; do not reset the worktree or touch accepted tests, package, receipts or frozen artifacts.

## Preserved-evidence search addendum (2026-11-10)

This addendum advances only the installed-evidence search. The preceding accepted inventory and inert qualification are preserved without rerunning them. On entry this file was already modified: 40,727 bytes, raw SHA-256 `ef9675f615a138676cd6793dd6fb87f7344ac27fd8377402ccf0b568e7cdbce9`. All those bytes remain an unchanged prefix. The earlier statements about a clean pre-task status and HEAD-only rollback describe the earlier inventory task, not this addendum. For this task rollback must restore the 40,727-byte pre-task snapshot, not the one-heading HEAD blob. The retained `R/bc5855e6-41c3-4f26-b895-10d637ad6ec3.before.py` has exactly that byte count and hash; verify both before using it. No rejection has been received.

### Search boundary and reproducibility

Started from `R/7c28f513-0f81-4325-86a5-ebe77a9fab35.jsonl` and `V/installation-verification-v3.json`. The review references `R/a268b82f-1294-492e-ac4d-b0854db49f15.jsonl`, its `.before.py`, and the V records; these were inspected inside the boundary. Recursively enumerated regular files under V, A and R only, excluding reparse-point entries and never following embedded production, interpreter, attempt or other external paths. Every enumerated file was read as bytes and compared with all 97 campaign pin values. JSONL command/output fields, source backups, fixture payloads and superseded V records were inspected as data. No recorded command was replayed. No project module was imported by the search.

V: 12 files, 114,324 bytes; A: 124 files, 3,275,591 bytes. Canonical manifest hashes are respectively `304574f81cdc360f49e335f98ac5d18087f247c34250dcfe629ea926f66cd712` and `26cd41d30ec7ccd5e411874c842a1b8b8b57c7706325db085d0ed8385426d586`. R had 132 files at enumeration; its current `bc5855e6-41c3-4f26-b895-10d637ad6ec3.jsonl` is the active task log and grows during inspection, so no immutable aggregate hash is asserted for R. Reproduction prints a per-file manifest and flags this live-log limitation. No archive/container file was present by filename extension; JSON strings and source excerpts are not byte-exact installed-file containers.

### Evidence identity and authentication

Raw hashes below authenticate reproducibility of the observed preserved bytes only. Cross-linked receipt hashes authenticate internal consistency of the review record, not independent installed-host origin, capture time, or owner attestation. No independently authenticated installed snapshot was discovered.

| Preserved record | Bytes | Raw SHA-256 | Basis / limitation |
| --- | ---: | --- | --- |
| `R/7c28f513-0f81-4325-86a5-ebe77a9fab35.jsonl` | 427188 | `7276c13498140af024becf3a52178f4b28a78ae246799738d7d5c5584b07bcae` | Review log; candidate reads, not installed capture |
| `R/7c28f513-0f81-4325-86a5-ebe77a9fab35.receipt.json` | 6668 | `7326a59db3f9cbeeb3f564d7899961554462126c23b75e3c785f34ef439a8d3e` | Review receipt; task.evidenceSha256 links prior log |
| `R/7c28f513-0f81-4325-86a5-ebe77a9fab35.diff` | 41229 | `7a9b3b914f49c9695408fa8f286701063aa26fd8b2e3aac733444443e2394226` | Candidate documentation diff; receipt.diffFileSha256 agrees |
| `R/a268b82f-1294-492e-ac4d-b0854db49f15.jsonl` | 293897 | `70412fb7fc2bd73ab15eafce024b44f05c2124b248502a10d79374655f356a61` | Prior inventory log; receipt evidence hash agrees |
| `V/installation-verification-v3.json` | 1718 | `3ab4ba0d58a880c729f3f4b4725b2b1f3eeac627fb388fb1a418b0013ca4dbaf` | Replacement digest declarations; no source payload |
| `A/campaign-installation-proposal.md` | 1381 | `1ddf936c47dab8b86e88655a6d14b9d237c14d56a03006758216203f4c541cbb` | Inactive proposal; NO-GO, no installation authority |
| `A/campaign-admission-decision.md` | 2066 | `b9f25b870cd6c1f0fe0a1f32d9411ad18032c57e21ea2dda82d0818fb28335a8` | NO-GO; says V3 lacks campaign admission inventory |

The review receipt names runtime-identity as PROGRESS; it does not certify installation. Review item_2 reads the prior log; item_4 reads candidate producer with `Get-Content ... -TotalCount 95`; prior inventory item_8 reads its first 45 lines and item_5 shows the correction Git diff. These are partial, text-decoded candidate/Git excerpts. Neither their output strings nor nested copies supply the original installed raw producer. Review item_7 repeats the 97-pin declarations and prior no-authority test output. That test output identifies no frozen runtime installation.

V contains only three generations of four JSON declarations: current, `superseded-consent-provenance/`, and `superseded-policy-draft/`. The two superseded installed bindings still declare production HEAD `485a46c1b3a2b26170f15ae415783f93d7cab753`, pre-install revision `630b1515a03a8d0b10eb0d081ca17c631ad32530`, candidate `01b4ae6f7b468d5924322816da1d6c4520886011`, the same V3 proposed argv, interpreter pin and referee entry. They supply no raw replacement backups or launch capture. All V file hashes are reproducible with the script below.

### Payloads found and excluded from installed identity

All R `*.before.py` payloads are listed here to avoid mistaking their suffix for installed source. Contents identify test or documentation backups; the local review/task records provide provenance, with no installed-host capture authentication.

| R backup | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `460e1cd8-2c44-4a37-9726-c91056d9acdd.before.py` | 20468 | `0fd1e4115272ce8311135accf71456db1456e9e69b2668de6eb41e5b833f1756` |
| `7d328cdc-7819-43da-a583-05c880ce66e6.before.py` | 8861 | `05b90a090c14e2d79056bc7b1ec9f888bd20f4ba44302f0b4ba1005fce6bf52f` |
| `821f2569-901f-46ab-8d3d-3e344db474a9.before.py` | 21352 | `656b446a2a0156a45d6e252fc9250ad093ce440a63558efc923ac94ff6fd3607` |
| `a268b82f-1294-492e-ac4d-b0854db49f15.before.py` | 39 | `2c8919d175d1c96357e7b6b8e4267d6403ab729ed79580a5ad6a5be3d8de6a38` |
| `bc5855e6-41c3-4f26-b895-10d637ad6ec3.before.py` | 40727 | `ef9675f615a138676cd6793dd6fb87f7344ac27fd8377402ccf0b568e7cdbce9` |
| `c3f39849-29de-4061-92b1-7f4ccdea6e8b.before.py` | 25531 | `2b0e14fc200f967c6fe7f1362567015334c44fbc38f1e5e468baa513e5e07e01` |
| `c7d1a327-f701-499b-9ff1-988308d34b2c.before.py` | 56 | `18eb3caf71ec6251299cea3ddd895c15fa60ec6a2812fd4e7b4f1c2fd24e68dd` |
| `e236ac38-bf58-4553-9fc8-2a0b00088127.before.py` | 23695 | `fc0a26435b14e200894e1414d754a8eeb32ed05e46bfa746bf817ad00ac2ab7c` |
| `f7682b37-5c91-4e1f-ab01-599f891dd023.before.py` | 4097 | `876181698582021c112e912f51a0340e4dd70b32fb7e20a9cc464b8ec34d2709` |
| `faaae693-d86d-499c-a333-5dfabefd1f19.before.py` | 11794 | `f2d6d428059513c90c6a1769993b825c29fe053a903ae77711fb17f6b17d1d2d` |

A contains four `inert.py` copies, under `{ora-al02-campaign-qualification-rwr5gm0a,ora-al02-campaign-qualification-zxmrawqt}/{controller-positive-uptake,controller-transitions}/`. Each is 1,926 bytes, raw SHA-256 `8ab162c73d4504fbd38a88c4b914c1b3e8d3fe8d8f3fca0de5a5100c6f08ecc0`; its own docstring identifies an inert relay child. These are fixture programs, not installed producer/runtime captures. A binary payloads are JSON branch/event fixtures: 84,235 bytes, `e136d0e1a10895b2e500766026957ed987f0a9cd4365776f589797eac9a416d7`, or 249,871 bytes, `1c6332c61c101402c5b16cebafa8a0bb3df70e411ef6e0f49619d129bbb1059d`. Their `lawful.bin` and `raw.bin` copies have fixture preservation provenance only. The reproduction manifest identifies each exact path; no fixture was executed.

Whole-file comparison against every pin found no nonempty match. Empty locks, stderr and diff files share SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` with the frozen empty `Lib/urllib/__init__.py`; this is byte equality without runtime-file provenance and closes zero pins. Thus authenticated installed coverage remains **0/97**: producer unavailable; the other 13 project payloads unavailable; all 83 interpreter/runtime payloads unavailable. The prior 13 candidate matches and producer mismatch are unchanged. No new authenticated producer exists for a raw-byte/AST comparison with frozen `266677b97c920a11359f818943c17aef240578b8cf58220c14d9d5333a1a0279`, candidate `6d822b98540968fe94ef4a21624af91974d715537b582d869372cee78f55acc4`, or Git blob `10df7acd0ca2a09b8f8b10e98f3b56f6d08d9c66`. The recorded blob and its normalized comparison remain candidate evidence, not reconstructed installation evidence. No newline/overlay cause is newly established.

### Launch identity, authority and smallest next scopes

| Identity | Available preserved evidence | Unresolved / smallest separately scoped correction |
| --- | --- | --- |
| argv and CWD | V proposed command; A frozen checkout and prior static command template | No authenticated actual launch argv/CWD. Obtain an already preserved launch record with exact argument boundaries, CWD, timestamp, process/owner and capture provenance; keep proposed and observed fields separate. |
| Interpreter | Declared path and SHA-256 in V/A; review/test commands refer to other launch contexts | Missing original interpreter/runtime payloads and authenticated version/executable identity from the relevant launch. Obtain retained bytes mapped to all 83 runtime pins; never infer from the inspection Python. |
| Simulator/referee | Frozen project pins and declared entry names; candidate excerpts | Missing installed module payloads, resolved module paths and actual entry mapping. Obtain retained simulator/referee closure and launch-linked mapping for all 14 project pins. |
| Revision / checkout / overlays | V historical HEAD, pre-install revision, candidate commit, Git blob declarations and replacement before/after digests; A frozen checkout | Missing installed Git observation, dirty/overlay inventory and byte-exact before/after capture chain. Obtain retained observations tied to the launch; HEAD alone cannot identify overlays. |
| Producer | Replacement digest declares AFTER `266677...`; candidate/Git excerpts identify reviewed correction | First inspect authenticated original raw AFTER payload and its provenance. If different, establish byte/AST cause before drafting a separately reviewed successor identity; do not modify frozen pins or guessed installation bytes. |

Historical V/A records remain authoritative for their recorded commitments; local candidate raw bytes and Git remain authoritative for reviewed candidate identity. Only an independently authenticated preserved capture could establish historical installed bytes and actual launch mapping. The review receipt authenticates its own review context only. No discovered source supersedes frozen records.

Exactly required preserved evidence: original raw producer AFTER bytes (and retained BEFORE backup if available), a manifest mapping original absolute paths to preserved payloads for every one of the 97 pins with sizes and raw hashes, capture timestamp and installed-host/owner identity, independently verifiable preservation/attestation chain, and contemporaneous launch argv/CWD/executable/version/module paths/Git revision/dirty-overlay observations bound to that same capture and terminal/admission identity. Declarations alone, copied digests, candidate Git blobs and inert receipts do not substitute for these payloads. If they were never preserved, this bounded search cannot retrospectively verify installation. Any new acquisition requires a separate scope; this task grants no production access.

Evidence-only engineering can still catalogue retained material, assess authentication and draft a successor identity for review. Source/pin correction and installation each require separate scoped authorization; science requires separate authorization even after engineering identity is resolved. Runtime identity stays OPEN. Accepted package, tests, frozen records, receipts and all None authority constants remain unchanged.

### Read-only reproduction for this addendum

Run from this candidate checkout using `python -B -`; the script imports only the standard library, reads only the three allowlisted roots, never interprets JSON paths as filesystem instructions, and prints exact manifest rows including backups/fixtures. Manifest SHA-256 uses sorted `[relative POSIX path, byte count, raw SHA-256]` rows, JSON `separators=(",", ":")`, `ensure_ascii=True`, UTF-8. R may change as the surrounding task logger appends; compare fixed evidence files individually.

```python
from pathlib import Path
import os, stat, json, hashlib
H = lambda b: hashlib.sha256(b).hexdigest()
roots = [Path('D:/OraLab/drafts/ora-al02-release-v3'),
         Path('D:/OraLab/reports/ora-al02-natural-b-panel-20261109'),
         Path('D:/OraLab/drafts/ora-director-cross-objective/runs')]
pins = json.loads((roots[1]/'campaign-binding.json').read_bytes())['pins']
for root in roots:
    rows = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(n for n in dirs if not (
            Path(directory, n).lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT))
        for name in sorted(names):
            p = Path(directory, name)
            if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                continue
            raw = p.read_bytes()
            rows.append([p.relative_to(root).as_posix(), len(raw), H(raw)])
    rows.sort()
    for rel, size, digest in rows:
        print(root, rel, size, digest)
        for original, expected in pins.items():
            if digest == expected:
                print('BYTE_MATCH_ONLY_NOT_AUTHENTICATION', rel, original)
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode()
    print('MANIFEST', root, len(rows), sum(r[1] for r in rows), H(encoded))
```

Validation for this addendum: permitted exact_artifacts no-authority test PASS (1 test, 0.001s); git diff --check PASS. AST confirms all three authorization constants remain None. Accepted release package and continuation test retain raw hashes e41d1ec56dee21fd4763121f29adae3f583f88c5a0827bcaf0842f9f8773c07a and 5e2a4eb72cb0a57eebff15a8f3ceee6d8319755b7f35e34bf094b8b943c7389e. Only this document is modified; HEAD unchanged; no commit. The original 40,727-byte prefix was checked byte-for-byte by SHA-256. No installation, scientific dispatch, worker, custody, Job, World, network or new agent was invoked.


## Manifest reproduction correction and bounded recheck (2026-11-11)

This is a documentation-only correction following preserved review `R/4d498f97-544c-4cd5-a2d6-83f570bb249b.jsonl`: 176,014 bytes, raw SHA-256 `f9f946d792bbc80af8fe9741089ff57db66e838213e9469bfb0e700e7ad7e104`. Its final decision is REJECT for the manifest ordering discrepancy, not a finding of installed verification. Its receipt (12,832 bytes, SHA-256 `f7cf372f6ab69ad13b8bf4ff27eae5e71604a227a50557b6b5cdecd64fdd8aef`) declares that same log hash; this establishes internal linkage only. The prior statement that no rejection had been received describes the earlier task and is superseded by this review. No installation or scientific permission follows from this correction.

Before this edit, read-only enumeration and raw hashing of the same V/A/R boundary reproduced the discrepancy. No fixes preceded that inventory. The historical A digest `26cd41d30ec7ccd5e411874c842a1b8b8b57c7706325db085d0ed8385426d586` is valid for rows in Windows Path order. The published script's `rows.sort()` instead sorts relative POSIX path strings and produces **`61ae141d2a34c9e1529085a8c067d7317d6785cf87982afb9da2f4d497ef7861`**. Both describe the same 124 files and 3,275,591 bytes. Cause is established: ordering of paths, not changed payloads. V remains 12 files, 114,324 bytes, digest `304574f81cdc360f49e335f98ac5d18087f247c34250dcfe629ea926f66cd712` under either ordering. The POSIX digest is authoritative for reproducing the published script; retain the Windows digest as historical executor evidence. This paragraph corrects the earlier characterization of the A digest as canonical for that script.

To reproduce both digests, use the preceding read-only script unchanged through collection of `rows`, then use this block in place of its final encoding/manifest lines (the preceding `rows.sort()` is harmless). No JSON path is dereferenced:

```python
from pathlib import PureWindowsPath
for label, ordered in [
    ('POSIX_STRING', sorted(rows)),
    ('WINDOWS_PATH', sorted(rows, key=lambda row: PureWindowsPath(row[0]))),
]:
    encoded = json.dumps(ordered, separators=(",", ":"), ensure_ascii=True).encode()
    print('MANIFEST', label, root, len(ordered), sum(r[1] for r in ordered), H(encoded))
```

The bounded recheck compared every whole-file raw hash against all 97 frozen pin values: V/A/R nonempty matches were zero. A had four empty matches and R had 29, all without runtime-path provenance. These close zero pins. R at enumeration had 144 files, 4,793,251 bytes; its aggregate is deliberately not promoted to an immutable identity because the current `f404a774-41bd-4eef-8cff-5e51d8e03c0b.jsonl` is this task's growing log. No producer-named file or archive/executable/library snapshot candidate was found by the enumerated filenames. This result supplements the prior payload classification; whole-file nonmatches alone cannot disprove embedded payloads or authenticate their origin.

Additional R raw backups `0124ff02-1e07-4e32-8ae2-1aad4d0ec00d.before.py` and `f404a774-41bd-4eef-8cff-5e51d8e03c0b.before.py` are each 55,032 bytes, SHA-256 `1bf446f2df0b120d5670d95796e91b97b1263a101592253a1c9e795987ba0c29`, and equal this document's pre-task bytes. They are documentation snapshots, not installed producer captures. The former JSONL was empty at inspection; the latter records this read-only task. Neither supplies independent installed-host or launch authentication. Prior raw payload, declaration, candidate Git and inert-fixture classifications remain intact.

Installed identity remains OPEN: authenticated coverage **0/97** (14 project payloads, including producer, and 83 interpreter/runtime payloads). No authenticated producer bytes were available for comparison with frozen `266677b97c920a11359f818943c17aef240578b8cf58220c14d9d5333a1a0279`, candidate `6d822b98540968fe94ef4a21624af91974d715537b582d869372cee78f55acc4`, or recorded Git blob `10df7acd0ca2a09b8f8b10e98f3b56f6d08d9c66`; no producer cause or overlay identity is newly established. Exact actual argv/CWD/interpreter/version, simulator/referee resolution, installed revision/checkout and overlay capture provenance remain missing. Historical V/A commitments and reviewed candidate identity retain their separate authority; review receipts do not supersede either with installed evidence.

The smallest next engineering scope remains authentication and static comparison of already preserved original producer/runtime payloads plus their path/size/hash manifest and capture chain, linked to contemporaneous exact launch and dirty-overlay observations as specified above. If these were never retained, this search cannot recover historical identity. Production acquisition, source/pin correction, installation and scientific dispatch each require separately authorized scope; absence of science authorization does not prevent further preserved-evidence engineering. No successor pin or runtime repair is justified by this manifest correction.

All 55,032 pre-task bytes are retained as an unchanged prefix. Rollback for this task only: verify either named 55,032-byte backup against its raw hash and restore only this document, or retain exactly the verified first 55,032 bytes. Do not restore the one-heading HEAD blob or discard earlier inventory. No tests or execution modules were run in this stage; historical passing tests above remain historical evidence. No accepted package, source, pin, receipt, fixture or authority constant was edited, and no commit was made.
