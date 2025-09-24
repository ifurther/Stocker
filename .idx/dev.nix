# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-25.05"; # or "unstable"
  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python313
    pkgs.python313Packages.pip
    pkgs.pipenv
    pkgs.tree
    pkgs.google-cloud-sdk
  ];
  # Sets environment variables in the workspace
  env = { };
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "mhutchie.git-graph"
      "pkief.material-icon-theme"
      "redhat.vscode-yaml"
      "yzhang.markdown-all-in-one"
      "ms-toolsai.jupyter"
      "ms-python.python"
      "charliermarsh.ruff"
      "ms-python.debugpy"
      "ms-toolsai.jupyter-keymap"
      "ms-toolsai.jupyter-renderers"
      "ms-toolsai.vscode-jupyter-cell-tags"
      "ms-toolsai.vscode-jupyter-slideshow"
      "saoudrizwan.claude-dev"
      "codezombiech.gitignore"
      "luma.jupyter"
      "usernamehw.errorlens"
      "oderwat.indent-rainbow"
      "aaron-bond.better-comments"
      "tamasfe.even-better-toml"
      "googlecloudtools.-dataconnect-vscode"
    ];
    # Enable previews
    previews = {
      enable = true;
      previews = {
        # web = {
        #   # Example: run "npm run dev" with PORT set to IDX's defined port for previews,
        #   # and show it in IDX's web preview panel
        #   command = ["npm" "run" "dev"];
        #   manager = "web";
        #   env = {
        #     # Environment variables to set for your server
        #     PORT = "$PORT";
        #   };
        # };
      };
    };
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # install-vscode-extensions = ''
        #   # Ensure .vscode/extensions.json exists
        #   if [ -f .vscode/extensions.json ]; then
        #     echo "Installing VS Code extensions from .vscode/extensions.json..."

        #     # Use jq to extract the extensions and install them
        #     jq -r '.recommendations[]' .vscode/extensions.json | while read -r EXTENSION; do
        #       echo "Installing $EXTENSION..."
        #       code --install-extension "$EXTENSION"
        #     done
        #   else
        #     echo ".vscode/extensions.json not found. Skipping extension installation."
        #   fi
        # '';
        # add-vscode-to-gitignore = ''
        #   # Add .vscode/ to .gitignore if it's not already there
        #   if ! grep -qxF '.vscode/' .gitignore 2>/dev/null; then
        #     echo '.vscode/' >> .gitignore
        #     echo "Added .vscode/ to .gitignore"
        #   else
        #     echo ".vscode/ already in .gitignore"
        #   fi
        # '';

        remove-template-artifacts = ''
          echo "Removing template artifacts..."
          rm -rf .git
          rm -f README.md
        '';
      };
      # Runs when the workspace is (re)started
      onStart = {
        setting-up-dev-env = ''
          pipenv install
        '';
        # Example: start a background task to watch and re-build backend code
        # watch-backend = "npm run watch-backend";
        # update-vscode-extensions = ''
        #   echo "Updating all installed VS Code extensions..."
        #   code --list-extensions | while read -r EXTENSION; do
        #     echo "Updating $EXTENSION..."
        #     code --force --install-extension "$EXTENSION"
        #   done
        # '';
      };
    };
  };
}