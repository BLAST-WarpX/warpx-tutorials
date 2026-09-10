###############################################################################
# WarpX tutorial Dockerfile
#
# Serves the tutorials as a browser-based JupyterLab session (notebooks +
# terminal) with a CPU and a CUDA kernel.
#
# Multi-stage build:
#   deps       compute-agnostic dependencies    -> /opt/deps, /opt/venv
#              (ADIOS2, openPMD-api incl. its Python bindings, and the
#               shared Python analysis stack)
#   build-cpu  OpenMP flavor   -> /opt/warpx-cpu + /opt/venv-cpu
#   build-gpu  CUDA flavor     -> /opt/warpx-gpu + /opt/venv-gpu
#   tutorial   CUDA *base* image + only the CUDA libraries we actually use,
#              plus the installed artifacts - no toolchain, no headers
#
# Sharing, so that nothing compute-agnostic is built or shipped twice:
#   * ADIOS2 and openPMD-api are built once in `deps`. Both venvs import the
#     one openPMD-api Python module, so the reader is guaranteed to be the
#     same build as the writer - the PyPI openpmd-api wheel would instead
#     vendor its own second copy of ADIOS2 and HDF5 into each venv.
#   * The Python analysis stack is installed once into /opt/venv; the flavor
#     venvs pick it up with a .pth file and hold only what is flavor-specific
#     (pywarpx, amrex, impactx, plus cupy on GPU and JupyterLab on CPU).
#   * Within a flavor, AMReX and pyAMReX are built once and shared by WarpX
#     and ImpactX (-DWarpX_amrex_internal=OFF etc.).
# Everything is built as shared libraries, which is also what lets the Python
# modules share AMReX's globals.
#
# Python environments are pip venvs, not conda: the conda `cuda` metapackage
# alone used to ship the entire CUDA toolkit inside the runtime image.
###############################################################################
ARG CUDA_VERSION=12.8.1
ARG UBUNTU_VERSION=24.04


###############################################################################
# Stage: deps - compute-agnostic dependencies
###############################################################################
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS deps

ARG NJOBS=4
ARG ADIOS2_VERSION=2.10.2
# Keep in sync with WarpX_openpmd_branch in
# warpx/cmake/dependencies/openPMD.cmake (WarpX requires >= 0.17.0).
ARG OPENPMD_VERSION=0.17.1

ENV DEBIAN_FRONTEND=noninteractive \
    CMAKE_GENERATOR=Ninja

# Build-time only. libboost-dev is header-only in our use (QED table
# generation via PICSAR) and therefore never reaches the runtime stage.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        git \
        libboost-dev \
        libbz2-dev \
        libfftw3-dev \
        libhdf5-dev \
        libzstd-dev \
        ninja-build \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# ADIOS2 provides the openPMD "bp" backend used by the two-stream, Weibel,
# TNSA and FODO inputs. No tutorial input configures a compression operator,
# so all compression engines stay off (this also drops the c-blosc2 build).
RUN git clone --branch v${ADIOS2_VERSION} --depth 1 \
        https://github.com/ornladios/ADIOS2.git /tmp/adios2 \
 && cmake -S /tmp/adios2 -B /tmp/adios2-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/deps \
        -DCMAKE_INSTALL_RPATH=/opt/deps/lib \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DADIOS2_USE_Blosc2=OFF \
        -DADIOS2_USE_BZip2=OFF \
        -DADIOS2_USE_DataMan=OFF \
        -DADIOS2_USE_Fortran=OFF \
        -DADIOS2_USE_HDF5=OFF \
        -DADIOS2_USE_MGARD=OFF \
        -DADIOS2_USE_MPI=OFF \
        -DADIOS2_USE_PNG=OFF \
        -DADIOS2_USE_Python=OFF \
        -DADIOS2_USE_SST=OFF \
        -DADIOS2_USE_SZ=OFF \
        -DADIOS2_USE_ZeroMQ=OFF \
        -DADIOS2_USE_ZFP=OFF \
        -DADIOS2_BUILD_EXAMPLES=OFF \
        -DBUILD_TESTING=OFF \
 && cmake --build /tmp/adios2-build --target install -j ${NJOBS} \
 && rm -rf /tmp/adios2 /tmp/adios2-build

# openPMD-api, C++ library and Python bindings, built once against the ADIOS2
# above and apt's HDF5. WarpX and ImpactX consume the C++ library
# (*_openpmd_internal=OFF) and both venvs import the Python module, so writer
# and reader always agree on the backend versions.
#
# The Python module lands in a Debian-flavored path for /usr/bin/python3, so
# normalize it to a stable symlink the venvs can point a .pth file at.
RUN git clone --branch ${OPENPMD_VERSION} --depth 1 \
        https://github.com/openPMD/openPMD-api.git /tmp/openpmd \
 && cmake -S /tmp/openpmd -B /tmp/openpmd-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/deps \
        -DCMAKE_PREFIX_PATH=/opt/deps \
        -DCMAKE_INSTALL_RPATH=/opt/deps/lib \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DopenPMD_USE_ADIOS2=ON \
        -DopenPMD_USE_HDF5=ON \
        -DopenPMD_USE_MPI=OFF \
        -DopenPMD_USE_PYTHON=ON \
        -DopenPMD_BUILD_EXAMPLES=OFF \
        -DopenPMD_BUILD_TESTING=OFF \
        -DPython_EXECUTABLE=/usr/bin/python3 \
 && cmake --build /tmp/openpmd-build --target install -j ${NJOBS} \
 && OPENPMD_PY_DIR=$(dirname "$(find /opt/deps -maxdepth 5 -type d -name openpmd_api | head -1)") \
 && test -n "${OPENPMD_PY_DIR}" \
 && test -d "${OPENPMD_PY_DIR}" \
 && ln -s "${OPENPMD_PY_DIR}" /opt/deps/python \
 && rm -rf /tmp/openpmd /tmp/openpmd-build

# Shared analysis stack. Every one of these is a pure-Python or manylinux
# wheel with no compute-backend flavor, so it is installed once here and both
# flavor venvs put it on sys.path with a .pth file. Keeping it out of the
# flavor venvs avoids ~370 MB of duplication (scipy, pandas, matplotlib and
# the IPython machinery are the bulk of it).
#
# Note: no PYTHONDONTWRITEBYTECODE anywhere in this build. /opt/venv* is
# root-owned and the tutorial runs unprivileged, so a missing .pyc could
# never be written later - every kernel start would recompile the stack.
RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-cache-dir \
        imageio \
        ipykernel \
        ipython \
        ipywidgets \
        matplotlib \
        numpy \
        openpmd-viewer \
        pandas \
        scipy \
 && /opt/venv/bin/python -c "import site, pathlib; pathlib.Path(site.getsitepackages()[0], 'openpmd-deps.pth').write_text('/opt/deps/python\n')" \
 && /opt/venv/bin/python -c "import openpmd_api, openpmd_viewer; print('shared stack ok', openpmd_api.__version__)"


###############################################################################
# Stage: build-cpu - OpenMP flavor
###############################################################################
FROM deps AS build-cpu

ARG NJOBS=4
ARG WARPX_VERSION=26.09
ARG IMPACTX_VERSION=26.09

ENV PREFIX=/opt/warpx-cpu \
    VENV=/opt/venv-cpu \
    CMAKE_PREFIX_PATH=/opt/deps:/opt/warpx-cpu

# The WarpX source tree stays around: it pins the AMReX/pyAMReX versions we
# build below, and ImpactX consumes it as its ABLASTR source.
RUN git clone --branch ${WARPX_VERSION} --depth 1 \
        https://github.com/BLAST-WarpX/warpx.git /tmp/warpx-src

# Shared AMReX. Options mirror what WarpX sets for its internal build
# (warpx/cmake/dependencies/AMReX.cmake) so that WarpX's later
# find_package(AMReX ... COMPONENTS ...) is satisfied.
RUN AMREX_TAG=$(python3 -c "import json;print(json.load(open('/tmp/warpx-src/dependencies.json'))['commit_amrex'])") \
 && git clone --branch ${AMREX_TAG} --depth 1 \
        https://github.com/AMReX-Codes/amrex.git /tmp/amrex \
 && cmake -S /tmp/amrex -B /tmp/amrex-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DAMReX_SPACEDIM="1;2;3" \
        -DAMReX_GPU_BACKEND=NONE \
        -DAMReX_OMP=ON \
        -DAMReX_MPI=OFF \
        -DAMReX_PARTICLES=ON \
        -DAMReX_PRECISION=DOUBLE \
        -DAMReX_PARTICLES_PRECISION=DOUBLE \
        -DAMReX_PIC=ON \
        -DAMReX_FFT=ON \
        -DAMReX_EB=ON \
        -DAMReX_LINEAR_SOLVERS=ON \
        -DAMReX_LINEAR_SOLVERS_EM=ON \
        -DAMReX_LINEAR_SOLVERS_INCFLO=ON \
        -DAMReX_TINY_PROFILE=ON \
        -DAMReX_ASSERTIONS=OFF \
        -DAMReX_FPE=OFF \
        -DAMReX_FASTMATH=OFF \
        -DAMReX_AMRLEVEL=OFF \
        -DAMReX_FORTRAN=OFF \
        -DAMReX_PROBINIT=OFF \
        -DAMReX_ENABLE_TESTS=OFF \
        -DAMReX_BUILD_TUTORIALS=OFF \
 && cmake --build /tmp/amrex-build --target install -j ${NJOBS} \
 && rm -rf /tmp/amrex /tmp/amrex-build

# Flavor venv, created only now that the non-Python stack is built, so that
# editing the package lists below does not invalidate the AMReX layer.
# It holds only what is flavor-specific; the shared analysis stack and the
# openPMD-api module come in via the .pth file.
# JupyterLab lives here only - this venv runs the server; the GPU venv is
# only ever a kernel. imageio-ffmpeg (a ~77 MB bundled encoder) likewise: the
# notebooks that write libx264 mp4 are analysis notebooks and run on the CPU
# kernel.
RUN python3 -m venv ${VENV} \
 && ${VENV}/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && ${VENV}/bin/pip install --no-cache-dir \
        imageio-ffmpeg \
        jupyterlab \
 && ${VENV}/bin/python -c "import site, sys, pathlib; v=f'python{sys.version_info.major}.{sys.version_info.minor}'; pathlib.Path(site.getsitepackages()[0], 'shared-deps.pth').write_text(f'/opt/venv/lib/{v}/site-packages\n/opt/deps/python\n')" \
 && ${VENV}/bin/python -c "import openpmd_api, openpmd_viewer, numpy, scipy, matplotlib, ipykernel; print('shared stack visible')"

# Shared pyAMReX. pyAMReX_CODES must list BOTH codes: WarpX asks for the
# CODES_WarpX component and ImpactX for CODES_ImpactX.
RUN PYAMREX_TAG=$(python3 -c "import json;print(json.load(open('/tmp/warpx-src/dependencies.json'))['commit_pyamrex'])") \
 && git clone --branch ${PYAMREX_TAG} --depth 1 \
        https://github.com/AMReX-Codes/pyamrex.git /tmp/pyamrex \
 && cmake -S /tmp/pyamrex -B /tmp/pyamrex-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DpyAMReX_amrex_internal=OFF \
        -DpyAMReX_CODES="WarpX;ImpactX" \
        -DpyAMReX_IPO=OFF \
        -DpyAMReX_BUILD_TESTING=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/pyamrex-build --target install -j ${NJOBS} \
 && cmake --build /tmp/pyamrex-build --target pip_install -j ${NJOBS} \
 && rm -rf /tmp/pyamrex /tmp/pyamrex-build

# WarpX. FFT is mandatory: four tutorial inputs use warpx.poisson_solver = fft.
# No RZ: every tutorial input is geometry.dims 1, 2 or 3. Leaving RZ out also
# drops the BLAS++/LAPACK++ dependency entirely, which WarpX requires only for
# RZ together with FFT (warpx/CMakeLists.txt:242-248).
# QED table generation is on (header-only Boost).
RUN cmake -S /tmp/warpx-src -B /tmp/warpx-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DWarpX_amrex_internal=OFF \
        -DWarpX_pyamrex_internal=OFF \
        -DWarpX_openpmd_internal=OFF \
        -DWarpX_COMPUTE=OMP \
        -DWarpX_DIMS="1;2;3" \
        -DWarpX_FFT=ON \
        -DWarpX_MPI=OFF \
        -DWarpX_PYTHON=ON \
        -DWarpX_QED_TABLE_GEN=ON \
        -DWarpX_IPO=OFF \
        -DWarpX_PYTHON_IPO=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/warpx-build --target install -j ${NJOBS} \
 && cmake --build /tmp/warpx-build --target pip_install -j ${NJOBS} \
 && ln -s ${PREFIX}/bin/warpx.1d* ${PREFIX}/bin/warpx.1d \
 && ln -s ${PREFIX}/bin/warpx.2d* ${PREFIX}/bin/warpx.2d \
 && ln -s ${PREFIX}/bin/warpx.3d* ${PREFIX}/bin/warpx.3d \
 && rm -rf /tmp/warpx-build

# ImpactX, reusing this flavor's AMReX and pyAMReX, the shared openPMD-api,
# and the WarpX source tree as ABLASTR. FFT stays off: the only ImpactX
# tutorial sets simulation.space_charge = False.
RUN git clone --branch ${IMPACTX_VERSION} --depth 1 \
        https://github.com/BLAST-ImpactX/impactx.git /tmp/impactx-src \
 && cmake -S /tmp/impactx-src -B /tmp/impactx-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DImpactX_ablastr_src=/tmp/warpx-src \
        -DImpactX_amrex_internal=OFF \
        -DImpactX_pyamrex_internal=OFF \
        -DImpactX_openpmd_internal=OFF \
        -DImpactX_COMPUTE=OMP \
        -DImpactX_FFT=OFF \
        -DImpactX_MPI=OFF \
        -DImpactX_PYTHON=ON \
        -DImpactX_PYTHON_IPO=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/impactx-build --target install -j ${NJOBS} \
 && cmake --build /tmp/impactx-build --target pip_install -j ${NJOBS} \
 && ln -s ${PREFIX}/bin/impactx.* ${PREFIX}/bin/impactx \
 && rm -rf /tmp/impactx-src /tmp/impactx-build /tmp/warpx-src

# Build-time leftovers. Headers and CMake/pkg-config metadata are only needed
# by the builds above, which are done. The *_pybind*.so are Python extension
# modules that the install targets duplicate into the prefix; pip_install
# already placed them in the venv and nothing links the prefix copies, so
# they are ~270 MB of dead weight in the CUDA flavor.
# --strip-debug is safe for CUDA fatbins (they live in allocated data
# sections); --strip-unneeded buys nothing here, these libraries are device
# code rather than symbols.
RUN rm -rf ${PREFIX}/include ${PREFIX}/lib/cmake ${PREFIX}/lib/pkgconfig \
 && rm -f ${PREFIX}/lib/*.a \
 && rm -f ${PREFIX}/lib/*pybind*.so \
 && find ${PREFIX}/lib ${PREFIX}/bin ${VENV} -type f -name '*.so*' \
        -exec strip --strip-debug {} + 2>/dev/null || true \
 && rm -rf /root/.cache


###############################################################################
# Stage: build-gpu - CUDA flavor
#
# Identical to build-cpu except for the compute backend. Keep the two in sync.
###############################################################################
FROM deps AS build-gpu

ARG NJOBS=4
ARG CUDAARCHS=75
ARG WARPX_VERSION=26.09
ARG IMPACTX_VERSION=26.09

ENV PREFIX=/opt/warpx-gpu \
    VENV=/opt/venv-gpu \
    CMAKE_PREFIX_PATH=/opt/deps:/opt/warpx-gpu

RUN git clone --branch ${WARPX_VERSION} --depth 1 \
        https://github.com/BLAST-WarpX/warpx.git /tmp/warpx-src

# AMReX_GPU_RDC=OFF, matching what WarpX forces for its own internal AMReX
# build (warpx/cmake/dependencies/AMReX.cmake:129-133). Relocatable device
# code would be nicer for extensibility, but it does not currently work here:
# with RDC every translation unit is device-linked together and WarpX 26.09
# overflows the 64 KB constant bank at nvlink,
#   "uses too much data for compiler-generated constants;
#    please recompile with -Xptxas --disable-optimizer-constants"
# across dozens of kernels. Enabling RDC again needs that -Xptxas workaround,
# which disables an optimizer feature globally.
RUN AMREX_TAG=$(python3 -c "import json;print(json.load(open('/tmp/warpx-src/dependencies.json'))['commit_amrex'])") \
 && git clone --branch ${AMREX_TAG} --depth 1 \
        https://github.com/AMReX-Codes/amrex.git /tmp/amrex \
 && cmake -S /tmp/amrex -B /tmp/amrex-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DAMReX_SPACEDIM="1;2;3" \
        -DAMReX_GPU_BACKEND=CUDA \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -DAMReX_GPU_RDC=OFF \
        -DAMReX_OMP=OFF \
        -DAMReX_MPI=OFF \
        -DAMReX_PARTICLES=ON \
        -DAMReX_PRECISION=DOUBLE \
        -DAMReX_PARTICLES_PRECISION=DOUBLE \
        -DAMReX_PIC=ON \
        -DAMReX_FFT=ON \
        -DAMReX_EB=ON \
        -DAMReX_LINEAR_SOLVERS=ON \
        -DAMReX_LINEAR_SOLVERS_EM=ON \
        -DAMReX_LINEAR_SOLVERS_INCFLO=ON \
        -DAMReX_TINY_PROFILE=ON \
        -DAMReX_ASSERTIONS=OFF \
        -DAMReX_FPE=OFF \
        -DAMReX_FASTMATH=OFF \
        -DAMReX_AMRLEVEL=OFF \
        -DAMReX_FORTRAN=OFF \
        -DAMReX_PROBINIT=OFF \
        -DAMReX_ENABLE_TESTS=OFF \
        -DAMReX_BUILD_TUTORIALS=OFF \
 && cmake --build /tmp/amrex-build --target install -j ${NJOBS} \
 && rm -rf /tmp/amrex /tmp/amrex-build

# Flavor venv, after the non-Python stack for the same cache reason as the CPU
# stage. No JupyterLab and no imageio-ffmpeg here: this venv is only ever a
# kernel, and the mp4-writing notebooks are analysis, i.e. the CPU kernel.
# cupy gives pyAMReX's .to_cupy() zero-copy access to GPU arrays; it is what
# makes the final stage need cuBLAS/cuSOLVER/cuSPARSE/NVRTC on top of the
# cuFFT and cuRAND our own binaries link.
RUN python3 -m venv ${VENV} \
 && ${VENV}/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && ${VENV}/bin/pip install --no-cache-dir \
        cupy-cuda12x \
 && ${VENV}/bin/python -c "import site, sys, pathlib; v=f'python{sys.version_info.major}.{sys.version_info.minor}'; pathlib.Path(site.getsitepackages()[0], 'shared-deps.pth').write_text(f'/opt/venv/lib/{v}/site-packages\n/opt/deps/python\n')" \
 && ${VENV}/bin/python -c "import openpmd_api, openpmd_viewer, numpy, scipy, matplotlib, ipykernel, cupy; print('shared stack visible, cupy', cupy.__version__)"

RUN PYAMREX_TAG=$(python3 -c "import json;print(json.load(open('/tmp/warpx-src/dependencies.json'))['commit_pyamrex'])") \
 && git clone --branch ${PYAMREX_TAG} --depth 1 \
        https://github.com/AMReX-Codes/pyamrex.git /tmp/pyamrex \
 && cmake -S /tmp/pyamrex -B /tmp/pyamrex-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -DpyAMReX_amrex_internal=OFF \
        -DpyAMReX_CODES="WarpX;ImpactX" \
        -DpyAMReX_IPO=OFF \
        -DpyAMReX_BUILD_TESTING=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/pyamrex-build --target install -j ${NJOBS} \
 && cmake --build /tmp/pyamrex-build --target pip_install -j ${NJOBS} \
 && rm -rf /tmp/pyamrex /tmp/pyamrex-build

RUN cmake -S /tmp/warpx-src -B /tmp/warpx-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -DWarpX_amrex_internal=OFF \
        -DWarpX_pyamrex_internal=OFF \
        -DWarpX_openpmd_internal=OFF \
        -DWarpX_COMPUTE=CUDA \
        -DWarpX_DIMS="1;2;3" \
        -DWarpX_FFT=ON \
        -DWarpX_MPI=OFF \
        -DWarpX_PYTHON=ON \
        -DWarpX_QED_TABLE_GEN=ON \
        -DWarpX_IPO=OFF \
        -DWarpX_PYTHON_IPO=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/warpx-build --target install -j ${NJOBS} \
 && cmake --build /tmp/warpx-build --target pip_install -j ${NJOBS} \
 && ln -s ${PREFIX}/bin/warpx.1d* ${PREFIX}/bin/warpx.1d \
 && ln -s ${PREFIX}/bin/warpx.2d* ${PREFIX}/bin/warpx.2d \
 && ln -s ${PREFIX}/bin/warpx.3d* ${PREFIX}/bin/warpx.3d \
 && rm -rf /tmp/warpx-build

RUN git clone --branch ${IMPACTX_VERSION} --depth 1 \
        https://github.com/BLAST-ImpactX/impactx.git /tmp/impactx-src \
 && cmake -S /tmp/impactx-src -B /tmp/impactx-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=${PREFIX} \
        -DCMAKE_INSTALL_RPATH="${PREFIX}/lib;/opt/deps/lib" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -DImpactX_ablastr_src=/tmp/warpx-src \
        -DImpactX_amrex_internal=OFF \
        -DImpactX_pyamrex_internal=OFF \
        -DImpactX_openpmd_internal=OFF \
        -DImpactX_COMPUTE=CUDA \
        -DImpactX_FFT=OFF \
        -DImpactX_MPI=OFF \
        -DImpactX_PYTHON=ON \
        -DImpactX_PYTHON_IPO=OFF \
        -DPython_EXECUTABLE=${VENV}/bin/python \
 && cmake --build /tmp/impactx-build --target install -j ${NJOBS} \
 && cmake --build /tmp/impactx-build --target pip_install -j ${NJOBS} \
 && ln -s ${PREFIX}/bin/impactx.* ${PREFIX}/bin/impactx \
 && rm -rf /tmp/impactx-src /tmp/impactx-build /tmp/warpx-src

RUN rm -rf ${PREFIX}/include ${PREFIX}/lib/cmake ${PREFIX}/lib/pkgconfig \
 && rm -f ${PREFIX}/lib/*.a \
 && rm -f ${PREFIX}/lib/*pybind*.so \
 && find ${PREFIX}/lib ${PREFIX}/bin ${VENV} -type f -name '*.so*' \
        -exec strip --strip-debug {} + 2>/dev/null || true \
 && rm -rf /root/.cache


###############################################################################
# Stages: export-* - CI artifact carriers
#
# A cold build of both flavors does not fit in one GitHub Actions job, so CI
# builds each flavor in its own job and pushes these scratch images (just the
# installed trees, no toolchain) to GHCR. The assemble job then substitutes
# them for the build-cpu / build-gpu stages:
#
#   docker buildx build --target tutorial \
#     --build-context build-cpu=docker-image://ghcr.io/<repo>/tutorial-artifacts:cpu-<sha> \
#     --build-context build-gpu=docker-image://ghcr.io/<repo>/tutorial-artifacts:gpu-<sha> .
#
# A plain local `docker build` ignores these stages and builds end-to-end.
###############################################################################
FROM scratch AS export-cpu
COPY --from=build-cpu /opt/deps      /opt/deps
COPY --from=build-cpu /opt/venv      /opt/venv
COPY --from=build-cpu /opt/warpx-cpu /opt/warpx-cpu
COPY --from=build-cpu /opt/venv-cpu  /opt/venv-cpu

FROM scratch AS export-gpu
COPY --from=build-gpu /opt/warpx-gpu /opt/warpx-gpu
COPY --from=build-gpu /opt/venv-gpu  /opt/venv-gpu


###############################################################################
# Stage: tutorial - the shipped image
###############################################################################
FROM nvidia/cuda:${CUDA_VERSION}-base-ubuntu${UBUNTU_VERSION} AS tutorial

ARG USER=tutorial
# CUDA library package suffix; keep in sync with CUDA_VERSION above.
ARG CUDA_PKG=12-8
ENV HOME=/home/${USER}

# Point matplotlib's cache at a writable, pre-created dir. Otherwise the first
# import warns and falls back to /tmp on every fresh container.
ENV MPLCONFIGDIR=${HOME}/.config/matplotlib

# The usual HDF5 quirk for various file systems and containers
ENV HDF5_USE_FILE_LOCKING=FALSE

# The CPU flavor is the default on PATH; `source /opt/venv-gpu/bin/activate`
# switches both Python and the warpx.* binaries to CUDA (see below).
# /opt/deps/bin adds openpmd-ls for inspecting BP/HDF5 output.
ENV PATH=/opt/venv-cpu/bin:/opt/warpx-cpu/bin:/opt/deps/bin:${PATH}

ENV DEBIAN_FRONTEND=noninteractive

# Runtime shared libraries only - no compilers, no headers, no CUDA toolkit.
#
# The CUDA libraries are hand-picked on top of the -base image rather than
# taking the -runtime image, which bundles a fixed superset: measured 2.69 GB
# vs 3.41 GB, so ~720 MB saved by leaving out NPP, nvJPEG, cuFile and NCCL.
# Our own binaries link only cuFFT and cuRAND; cuBLAS, cuSOLVER, cuSPARSE and
# NVRTC are here for cupy, which loads them dynamically. cuTENSOR and NCCL are
# optional cupy backends that nothing here uses, so they stay out.
#
# Ubuntu 24.04 carries t64 suffixes on several of these.
# libgomp1 is needed by BOTH flavors: the CPU build is OpenMP, and PICSAR's
# QED table generator links OpenMP even in the CUDA build.
# Both FFTW precisions are needed: AMReX_FFT=ON links libfftw3 *and*
# libfftw3f, so without libfftw3-single3 even `import impactx` fails.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        libbz2-1.0 \
        libfftw3-double3 \
        libfftw3-single3 \
        libgomp1 \
        libhdf5-103-1t64 \
        libhdf5-hl-100t64 \
        libzstd1 \
        python3 \
        python3-venv \
        supervisor \
        zlib1g \
        cuda-cudart-${CUDA_PKG} \
        cuda-nvrtc-${CUDA_PKG} \
        libcublas-${CUDA_PKG} \
        libcufft-${CUDA_PKG} \
        libcurand-${CUDA_PKG} \
        libcusolver-${CUDA_PKG} \
        libcusparse-${CUDA_PKG} \
        libnvjitlink-${CUDA_PKG} \
 && rm -rf /var/lib/apt/lists/*

# Non-root user to run the tutorial
RUN useradd --create-home --shell /bin/bash ${USER}

COPY --from=build-cpu /opt/deps      /opt/deps
COPY --from=build-cpu /opt/venv      /opt/venv
COPY --from=build-cpu /opt/warpx-cpu /opt/warpx-cpu
COPY --from=build-cpu /opt/venv-cpu  /opt/venv-cpu
COPY --from=build-gpu /opt/warpx-gpu /opt/warpx-gpu
COPY --from=build-gpu /opt/venv-gpu  /opt/venv-gpu

# Only /opt/deps goes into the global loader cache. The two flavor prefixes
# hold libraries with identical SONAMEs (libamrex_3d.so, libablastr_3d.so),
# so those must stay resolved per-binary via the RPATHs baked in above -
# never globally, or a CPU binary could load the CUDA library.
RUN echo "/opt/deps/lib" > /etc/ld.so.conf.d/warpx-deps.conf \
 && ldconfig

# Make `source .../activate` switch the warpx.* binaries too, so it is a
# drop-in for what `conda activate warpx-gpu` used to do. The line is appended
# after venv's own PATH bookkeeping, so `deactivate` still restores cleanly.
RUN echo 'export PATH="/opt/warpx-cpu/bin:$PATH"' >> /opt/venv-cpu/bin/activate \
 && echo 'export PATH="/opt/warpx-gpu/bin:$PATH"' >> /opt/venv-gpu/bin/activate

# Keep the kernel names the README already refers to. The GPU kernel needs an
# explicit PATH: it inherits the image-wide PATH otherwise, so a `!warpx.3d`
# or %%bash cell in a GPU notebook would silently run the CPU binary.
RUN /opt/venv-cpu/bin/python -m ipykernel install --prefix=/usr/local \
        --name warpx-cpu --display-name "WarpX CPU" \
 && /opt/venv-gpu/bin/python -m ipykernel install --prefix=/usr/local \
        --name warpx-gpu --display-name "WarpX GPU" \
 && python3 -c "\
import json, pathlib; \
p = pathlib.Path('/usr/local/share/jupyter/kernels/warpx-gpu/kernel.json'); \
d = json.loads(p.read_text()); \
d['env'] = {'PATH': '/opt/venv-gpu/bin:/opt/warpx-gpu/bin:/opt/deps/bin:/usr/local/bin:/usr/bin:/bin'}; \
p.write_text(json.dumps(d, indent=1))" \
 && mkdir -p ${MPLCONFIGDIR} \
 && chown -R ${USER}:${USER} ${HOME}

# Auto-activate the CPU environment in new terminals.
RUN printf '\nsource /opt/venv-cpu/bin/activate\n' >> ${HOME}/.bashrc \
 && chown ${USER}:${USER} ${HOME}/.bashrc

# Copy the whole repo; JupyterLab root is set in supervisord.conf.
COPY --chown=${USER}:${USER} . ${HOME}/warpx-tutorials/

# supervisord config, with the username substituted in.
COPY ./containers/tutorial/supervisord.conf /etc/supervisord.conf
RUN sed -i "s/XXX/${USER}/g" /etc/supervisord.conf

RUN touch /var/log/jupyter.log \
 && chown -R ${USER}:${USER} /var/log/jupyter.log

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/lab || exit 1

CMD ["/usr/bin/supervisord"]
