def api_parameter(parser):
    parser.add_argument(
        "--api",
        required=True,
        help="Telescope API server URL. Eg https://api.elec.ac.nz/tart/mu-udm",
    )
