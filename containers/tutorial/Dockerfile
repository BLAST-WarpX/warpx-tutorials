###############################################################################
# WarpX tutorial Dockerfile
#
# Runs JupyterLab (browser-based notebooks + terminal) under supervisord so
# tutorial participants can run WarpX and post-process results in their
# browser. WarpX and the post-processing stack are pre-installed into a conda
# environment named "warpx", pre-activated in terminals and pre-selected as the
# notebook kernel.
###############################################################################

FROM condaforge/miniforge3:latest

ARG USER=tutorial
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

# Pre-build the "warpx" environment: WarpX (serial/CPU from conda-forge) plus
# the post-processing stack the analysis notebooks import.
# Pin warpX version to match current tutorial content.
RUN mamba create -y -n warpx -c conda-forge \
        warpx=26.05 \
        openpmd-api openpmd-viewer yt h5py \
        numpy scipy pandas matplotlib fast-histogram numba \
        jupyterlab ipympl ipywidgets \
 && mamba clean -a -y

# Register "warpx" as kernel "warpx-pm-postproc" — the name the notebooks hardcode.
# The chown fixes root-owned ~/.ipython created by this step
RUN /opt/conda/envs/warpx/bin/python -m ipykernel install --prefix=/usr/local \
        --name warpx-pm-postproc --display-name "WarpX-PM-PostProcessing" \
 && mkdir -p ${MPLCONFIGDIR} \
 && chown -R ${USER}:${USER} ${HOME}

# Auto-activate "warpx" in new terminals. Running as root, we append directly
# to the user's .bashrc; `conda init bash` here would only touch root's.
RUN printf '\nsource /opt/conda/etc/profile.d/conda.sh\nconda activate warpx\n' >> ${HOME}/.bashrc \
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
