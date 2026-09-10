###############################################################################
# WarpX tutorial Dockerfile
#
# Runs JupyterLab (browser-based notebooks + terminal) under supervisord so
# tutorial participants can run WarpX and post-process results in their
# browser. CPU and CUDA-enabled WarpX environments are pre-installed and
# exposed as Jupyter kernels.
###############################################################################

FROM condaforge/miniforge3:latest

ARG USER=tutorial
ARG CUDAARCHS=75
ARG WARPX_VERSION=26.09
ARG BLASPP_VERSION=2025.05.28
ARG NJOBS=4
ENV HOME=/home/${USER}

# Point matplotlib's cache at a writable, pre-created dir. Otherwise the first
# import warns and falls back to /tmp on every fresh container.
ENV MPLCONFIGDIR=${HOME}/.config/matplotlib

# supervisor runs JupyterLab in the foreground
RUN apt-get update \
 && apt-get install -y --no-install-recommends supervisor curl git \
 && rm -rf /var/lib/apt/lists/*

# Non-root user to run the tutorial
RUN useradd --create-home --shell /bin/bash ${USER}

# Pre-build the CPU environment: WarpX (serial/CPU from conda-forge) plus the
# post-processing stack the analysis notebooks import.
RUN mamba create -y -n warpx-cpu -c conda-forge \
        warpx=${WARPX_VERSION} \
        openpmd-api openpmd-viewer yt h5py \
        numpy scipy pandas matplotlib fast-histogram numba \
        ipykernel jupyterlab ipympl ipywidgets \
 && mamba clean -a -y

# Install CUDA WarpX build dependencies.
RUN mamba create -y -n warpx-gpu -c nvidia -c conda-forge \
        boost ccache cmake compilers cuda cuda-nvtx-dev cupy fftw git \
        h5py ipykernel jupyterlab libblas libcblas liblapack liblapacke make matplotlib mamba ninja numpy \
        openpmd-api openpmd-viewer packaging pandas pip pkg-config python \
        python-build scipy setuptools virtualenv wheel yt \
 && mamba clean -a -y

# Build CUDA-enabled BLAS++ for WarpX RZ spectral solvers.
RUN curl -fsSL https://github.com/icl-utk-edu/blaspp/releases/download/v${BLASPP_VERSION}/blaspp-${BLASPP_VERSION}.tar.gz \
        | tar -xz -C /tmp \
 && mamba run -n warpx-gpu cmake -S /tmp/blaspp-${BLASPP_VERSION} -B /tmp/blaspp-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/conda/envs/warpx-gpu \
        -DCMAKE_PREFIX_PATH=/opt/conda/envs/warpx-gpu \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -Dgpu_backend=cuda \
        -Duse_openmp=OFF \
        -Duse_cmake_find_blas=ON \
        -DBLA_VENDOR=Generic \
        -Dblas_int="int (LP64)" \
        -Dbuild_tests=OFF \
 && mamba run -n warpx-gpu cmake --build /tmp/blaspp-build --target install -j ${NJOBS} \
 && rm -rf /tmp/blaspp-${BLASPP_VERSION} /tmp/blaspp-build

# Build CUDA-enabled LAPACK++ against the installed BLAS++ library.
RUN curl -fsSL https://github.com/icl-utk-edu/lapackpp/releases/download/v${BLASPP_VERSION}/lapackpp-${BLASPP_VERSION}.tar.gz \
        | tar -xz -C /tmp \
 && mamba run -n warpx-gpu cmake -S /tmp/lapackpp-${BLASPP_VERSION} -B /tmp/lapackpp-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/conda/envs/warpx-gpu \
        -DCMAKE_PREFIX_PATH=/opt/conda/envs/warpx-gpu \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -Dgpu_backend=cuda \
        -Duse_cmake_find_lapack=ON \
        -DBLA_VENDOR=Generic \
        -Dbuild_tests=OFF \
 && mamba run -n warpx-gpu cmake --build /tmp/lapackpp-build --target install -j ${NJOBS} \
 && rm -rf /tmp/lapackpp-${BLASPP_VERSION} /tmp/lapackpp-build

# Build serial CUDA WarpX from the same source version as the CPU package.
RUN git clone --branch ${WARPX_VERSION} --depth 1 https://github.com/BLAST-WarpX/warpx.git /tmp/warpx-src \
 && mamba run -n warpx-gpu cmake -S /tmp/warpx-src -B /tmp/warpx-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES=${CUDAARCHS} \
        -DCMAKE_INSTALL_PREFIX=/opt/conda/envs/warpx-gpu \
        -DCMAKE_PREFIX_PATH=/opt/conda/envs/warpx-gpu \
        -DWarpX_COMPUTE=CUDA \
        -DWarpX_DIMS="1;2;3;RZ" \
        -DWarpX_FFT=ON \
        -DWarpX_MPI=OFF \
        -DWarpX_PYTHON=ON \
 && mamba run -n warpx-gpu cmake --build /tmp/warpx-build --target install -j ${NJOBS} \
 && mamba run -n warpx-gpu cmake --build /tmp/warpx-build --target pip_install -j ${NJOBS} \
 && ln -s /opt/conda/envs/warpx-gpu/bin/warpx.1d* /opt/conda/envs/warpx-gpu/bin/warpx.1d \
 && ln -s /opt/conda/envs/warpx-gpu/bin/warpx.2d* /opt/conda/envs/warpx-gpu/bin/warpx.2d \
 && ln -s /opt/conda/envs/warpx-gpu/bin/warpx.rz* /opt/conda/envs/warpx-gpu/bin/warpx.rz \
 && ln -s /opt/conda/envs/warpx-gpu/bin/warpx.3d* /opt/conda/envs/warpx-gpu/bin/warpx.3d \
 && rm -rf /tmp/warpx-src /tmp/warpx-build \
 && mamba clean -a -y

# Keep the established CPU kernel name for notebooks and add a GPU kernel for
# simulations. The chown fixes root-owned ~/.ipython created by this step.
RUN /opt/conda/envs/warpx-cpu/bin/python -m ipykernel install --prefix=/usr/local \
        --name warpx-pm-postproc --display-name "WarpX CPU" \
 && /opt/conda/envs/warpx-gpu/bin/python -m ipykernel install --prefix=/usr/local \
        --name warpx-gpu --display-name "WarpX GPU" \
 && mkdir -p ${MPLCONFIGDIR} \
 && chown -R ${USER}:${USER} ${HOME}

# Auto-activate the CPU environment in new terminals. Running as root, we append directly
# to the user's .bashrc; `conda init bash` here would only touch root's.
RUN printf '\nsource /opt/conda/etc/profile.d/conda.sh\nconda activate warpx-cpu\n' >> ${HOME}/.bashrc \
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
