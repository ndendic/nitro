from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="nitro-boost",
    version="0.1.0",
    rust_extensions=[
        RustExtension(
            "nitro",
            binding=Binding.Exec,
            features=["pyo3/extension-module"],
            py_limited_api=False,
        ),
    ],
    packages=["nitro"],
    zip_safe=False,
    python_requires=">=3.12",
)
