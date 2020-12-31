import os
import sys
import platform
import subprocess
import cpt.packager

import boost

GCC = "gcc"
CLANG = "clang"
APPLE_CLANG = "apple-clang"
MSVC = "Visual Studio"

LINUX = platform.system() == "Linux"
MACOS = platform.system() == "Darwin"
WIN = platform.system() == "Windows"


def get_packio_reference():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    root = os.path.split(this_dir)[0]
    sys.path.insert(0, root)

    from conanfile import PackioConan

    return f"{PackioConan.name}/{PackioConan.version}"


def clear_local_cache():
    subprocess.check_call(["conan", "remove", "-f", get_packio_reference()])


class Packager(cpt.packager.ConanMultiPackager):
    def __init__(self):
        super().__init__(build_policy="missing", archs=["x86_64"])

    def add(
        self,
        compiler,
        compiler_version,
        cppstd,
        build_type="Release",
        settings=None,
        options=None,
    ):
        settings = settings or {}
        settings["compiler"] = compiler
        settings["compiler.version"] = compiler_version
        settings["build_type"] = build_type

        if compiler == CLANG and compiler_version == "11" and cppstd == "20":
            # FIXME: Clang 11 needs libc++ to have coroutines support
            settings["compiler.libcxx"] = "libc++"

        options = options or {}
        if "asio" not in options:
            options.update(self._get_boost_options(options.get("boost")))
        options["msgpack:cpp_api"] = True
        options["msgpack:c_api"] = False
        options["cppstd"] = cppstd

        unity_batch = os.environ.get("UNITY_BATCH", None)
        if unity_batch:
            options["unity_batch"] = unity_batch

        env_vars = {}
        if compiler == GCC:
            env_vars.update(
                {"CXX": f"g++-{compiler_version}", "CC": f"gcc-{compiler_version}"}
            )
        elif compiler == CLANG:
            if compiler_version == "7.0":
                compiler_version = "7"
            env_vars.update(
                {
                    "CXX": f"clang++-{compiler_version}",
                    "CC": f"clang-{compiler_version}",
                }
            )
        elif compiler == APPLE_CLANG:
            # This does not look good but its only designed to work
            # within github actions: at the moment clang 12 is detected
            # by default at a non-specified path and clang 11 is available
            # as clang-11
            if compiler_version == "11.0":
                env_vars.update(
                    {
                        "CXX": "clang-11",
                        "CC": "clang-11",
                    }
                )

        super().add(settings, options, env_vars)

    @staticmethod
    def _get_boost_options(boost_version):
        options = {}

        if (
            boost_version in ["1.70.0", "1.71.0", "1.72.0", "1.73.0", "1.74.0"]
            and not WIN
        ):
            options["boost:header_only"] = True
        else:
            LIBS_TO_KEEP = ["json", "container", "exception", "system"]
            for opt in [
                f"without_{lib}"
                for lib in boost.CONFIGURE_OPTIONS_1_75
                if lib not in LIBS_TO_KEEP
            ]:
                options[f"boost:{opt}"] = True

        return options


def test_linux():
    # easier to use on my ubuntu dev machine
    os.environ["CONAN_PIP_COMMAND"] = "pip3"

    builder = Packager()

    # fmt: off
    # Test supported GCC versions
    builder.add(compiler=GCC, compiler_version="7", cppstd="17")
    builder.add(compiler=GCC, compiler_version="8", cppstd="17")
    builder.add(compiler=GCC, compiler_version="9", cppstd="17")
    builder.add(compiler=GCC, compiler_version="10", cppstd="20")

    # Test supported clang versions
    builder.add(compiler=CLANG, compiler_version="6.0", cppstd="17")
    builder.add(compiler=CLANG, compiler_version="7.0", cppstd="17")
    builder.add(compiler=CLANG, compiler_version="8", cppstd="17")
    builder.add(compiler=CLANG, compiler_version="9", cppstd="17")
    builder.add(compiler=CLANG, compiler_version="10", cppstd="17")
    builder.add(compiler=CLANG, compiler_version="11", cppstd="20")

    # Test supported boost versions, with C++20 and coroutines from 1.74.0
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"boost": "1.70.0"})
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"boost": "1.71.0"})
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"boost": "1.72.0"})
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"boost": "1.73.0"})
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"boost": "1.74.0"})
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"boost": "1.75.0"})

    # Test supported asio versions, with C++20 and coroutines from 1.17.0
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"asio": "1.13.0", "packio:standalone_asio": True})
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"asio": "1.14.1", "packio:standalone_asio": True})
    builder.add(compiler=GCC, compiler_version="10", cppstd="17", options={"asio": "1.16.1", "packio:standalone_asio": True})
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"asio": "1.17.0", "packio:standalone_asio": True})
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"asio": "1.18.0", "packio:standalone_asio": True})
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"asio": "1.18.1", "packio:standalone_asio": True})

    # Test logs and debug build
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"loglevel": "trace"}, build_type="Debug")
    builder.add(compiler=GCC, compiler_version="10", cppstd="20", options={"loglevel": "trace"})
    # fmt: on

    builder.run()


def test_mac():
    builder = Packager()
    # fmt: off
    builder.add(compiler=APPLE_CLANG, compiler_version="12.0", cppstd="17", build_type="Debug")
    builder.add(compiler=APPLE_CLANG, compiler_version="12.0", cppstd="17")
    builder.add(compiler=APPLE_CLANG, compiler_version="12.0", cppstd="20", build_type="Debug")
    builder.add(compiler=APPLE_CLANG, compiler_version="12.0", cppstd="20")
    # fmt: on
    builder.run()


def test_windows():
    builder = Packager()
    # fmt: off
    builder.add(compiler=MSVC, compiler_version="16", cppstd="20", build_type="Debug")
    builder.add(compiler=MSVC, compiler_version="16", cppstd="20")
    builder.add(compiler=MSVC, compiler_version="16", cppstd="17", build_type="Debug")
    builder.add(compiler=MSVC, compiler_version="16", cppstd="17")
    # fmt: on
    builder.run()


def main():
    clear_local_cache()

    if LINUX:
        test_linux()
    elif MACOS:
        test_mac()
    elif WIN:
        test_windows()
    else:
        print(f"Unknown platform: {platform.system()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
