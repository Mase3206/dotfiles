# Authoring Mods

Authoring a mod is pretty easy. A mod is simply a class which subclasses `BaseMod` and defines its abstract methods and properties:

- `@property dependencies(self) -> list[str]`
- `@property dotfiles(self) -> list[str]`
- `detect(self, quiet = False) -> bool`
- `install(self)`

Implement those methods and properties in a class with a globally-unique name which subclasses `BaseMod` in the dotmgr/mods/ folder, and the dotfile manager (technically `dotmgr.mods.__init__`) will automatically find and store them.

A mod should also update the `status` property after detection and installation to reflect its actual status.