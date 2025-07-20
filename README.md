# Python packages for the TART radio telescope

There are three python packages that are used for various parts of the TART telescope.
In the  directory `tart/` is a general-use package. This contains imaging routines and many useful utilities for handling coordinate transformations e.t.c.
Meanwhile `tart_tools/` is a package that contains tools for the TART telescope. This contains tools for controlling and retrieving data from the TART telescope via CLI.

For everyday use, these can simply be installed using PyPi
```
     sudo pip install tart[all] tart_tools
```

or with [Astral.sh UV](https://docs.astral.sh/uv/getting-started/installation/)

```bash
    uv venv
    source .venv/bin/activate
    uv pip install tart tart_tools
```

## Authors

* Tim Molteno (tim@elec.ac.nz)
* Max Scheel (max@max.ac.nz)
* Tim Miller (timmiller83@gmail.com)
* Pat Suggate (ihavenolimbs@gmail.com)
