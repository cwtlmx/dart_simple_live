#!/usr/bin/env python3
"""Unify all subprojects (incl. plugins) Java/Kotlin JVM target to 17.

Flutter plugins hardcode their own Java/Kotlin targets (1.8, 11, 17) which clash
with the app's Kotlin 17 target, producing errors ON RANDOM PLUGINS:
    Inconsistent JVM Target Compatibility Between Java and Kotlin Tasks
        ... 'compileReleaseJavaWithJavac' (1.8) and 'compileReleaseKotlin' (17)

Editing each plugin is futile. Inject one block into the ROOT android/build.gradle.kts.

CRITICAL: the afterEvaluate registration MUST come BEFORE
    subprojects { project.evaluationDependsOn(":app") }
otherwise: "Cannot run Project.afterEvaluate(Action) when the project is already evaluated"

Usage: python3 patch_jvm_target.py <repo_root> <app_dir>
       python3 patch_jvm_target.py . simple_live_app
"""
import pathlib
import sys

BLOCK = '''// ==== 统一所有子项目(含插件) Java/Kotlin JVM target = 17 ====
subprojects {
    afterEvaluate {
        extensions.findByType<com.android.build.gradle.BaseExtension>()?.let { ext ->
            ext.compileOptions {
                sourceCompatibility = JavaVersion.VERSION_17
                targetCompatibility = JavaVersion.VERSION_17
            }
        }
        extensions.findByType<org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension>()?.let { k ->
            k.compilerOptions {
                jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
            }
        }
        tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
            compilerOptions {
                jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
            }
        }
        tasks.withType<JavaCompile>().configureEach {
            sourceCompatibility = "17"
            targetCompatibility = "17"
        }
    }
}

'''

ANCHOR = 'subprojects {\n    project.evaluationDependsOn(":app")\n}\n'


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    proj = sys.argv[2] if len(sys.argv) > 2 else "simple_live_app"
    p = root / proj / "android" / "build.gradle.kts"
    if not p.exists():
        print(f"NOT FOUND: {p}")
        return 1
    t = p.read_text()
    if "统一所有子项目" in t:
        print(f"{proj}: 已有 JVM 统一配置，跳过")
        return 0
    if ANCHOR not in t:
        print(f"{proj}: 未找到 evaluationDependsOn 锚点，请手工处理")
        return 1
    p.write_text(t.replace(ANCHOR, BLOCK + ANCHOR, 1))
    print(f"{proj}: 已注入 JVM target 统一配置 (17)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
