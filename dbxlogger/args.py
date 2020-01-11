def add_arguments_to(parser):
    """Add dbx arguments to the given argparse.ArgumentParser.

    The arguments are:
        --repo      the path of the repository where experiments are saved
        --name      the name of the experiment
    """

    parser.add_argument("--repo", type=str, default=None,
        help="Path where to save experiments")

    parser.add_argument("--name", type=str, default=None,
        help="Name of the experiment. Using current local timestamp if none given.")
