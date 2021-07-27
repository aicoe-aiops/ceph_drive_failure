# Get Started

The Jupyter notebooks in this project are intended to walk you through each phase of the machine learning workflow - data understanding and exploration, data cleaning, feature engineering, and model training. So going through these notebooks step-by-step is a great way to get started with the project.


## Launch Project and Run Notebooks via JupyterHub

To make the notebooks reproducible and executable by everyone, we have containerized and deployed them on the public [JupyterHub](https://jupyterhub-opf-jupyterhub.apps.zero.massopen.cloud) instance on the [Massachusetts Open Cloud](https://massopen.cloud/) (MOC). So you can get access to a Jupyter environment and run our notebooks in just a few clicks! To do so, please follow the steps below:

1. Visit our [JupyterHub](https://jupyterhub-opf-jupyterhub.apps.zero.massopen.cloud), click on `Log in with moc-sso` and sign in using your Google Account.
2. On the spawner page, select `Ceph Hard Drive Failure Prediction` for notebook image, `Large` for container size, and then click `Start server` to spawn your server.
3. Once your server has spawned, you should see a directory titled `ceph-drive-failure-<current-timestamp>`. All the notebooks should be available inside the `notebooks` directory in it for you to explore.


## Blog Post and Conference Talk

In addition to exploring the notebooks, you can also read our [blog post](./blog/hard-drive-failure-prediction-blog.md) to get a brief summary of the project. Or check out our [conference talk](https://www.youtube.com/watch?v=BXHIabjpARA) at DevConf.CZ 2020 for an in-depth presentation and discussion.
