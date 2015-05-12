# github-updater

A QGIS plugin to manage automatic updates of other QGIS plugins from a GitHub repo.

## Usage

If you want your QGIS plugin to update itself from a github repository, follow this instructions:

- Create a GitHub repository with the code of your plugin. It should have the same structure that will be needed to installed in the QGIS plugins folder. That is, if your plugin is called "myplugin" and it should have its python files under [qgis_plugins_folder]/myplugin, then the root of your repo must have a folder named "myplugin" with your plugin code.

You can add individual files in the repository root folder. They will not be copied to the QGIS plugins folder when installing. Only subfolders (there should be only one subfolder, as explained above) will be installed.

To better understand this, take a look at the structure of this repository, since it complies with those requirements.

- In your plugin code, add the following lines to the *initGui* and *unload* methods:

```
    def initGui(self):
        ...
        try:
            from github import addUpdatePluginMenu
            addUpdatePluginMenu("My plugin menu", "volaya", "github-updater")
        except ImportError:
            pass

    def unload(self):
        ...
        try:
            from github import removeUpdatePluginMenu
            removeUpdatePluginMenu("My plugin menu")
        except ImportError:
            pass
```

Replace *[My plugin menu]* with the name of the menu where you plugin menu item is located, and "volaya" and "github-updater" with the username and reponame corresponding to the repository where the plugin code is located.

Now there will be an additional menu in your plugin menu, which will allow the user to update the plugin from the GitHub repository.


- To create a release version, just create a tag in your GitHub repository
