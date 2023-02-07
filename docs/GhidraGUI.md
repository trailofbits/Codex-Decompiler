# Ghidra GUI Notes
This file is to provide some information about how to create GUI components in Ghidra from the plugin standpoint. When creating this plugin, there was no information about this online. Thus, I feel that it is important to provide this to the community to assist in plugin development.
Note: the code examples will be shown in Jython, but the classes and methods referenced should work for Java plugins as well.

## [PluginTool](https://ghidra.re/ghidra_docs/api/ghidra/framework/plugintool/PluginTool.html)
The PluginTool is a class that allows a developer to manage and interact with plugins within the Ghidra environment. An instance of this class can be accessed by calling:
```python
currentTool = state.getTool()
```
Using this instance, we can add ComponentProviders which are objects that "provide" a visual component or representation for a plugin. Here is the code for adding a ComponentProvider.
```python
currentTool = state.getTool()
#The second parameter is if the ComponentProvider should be visible or not.
currentTool.addComponentProvider(currentProvider, True)
```
## [ComponentProviderAdapter](https://ghidra.re/ghidra_docs/api/ghidra/framework/plugintool/ComponentProviderAdapter.html)
The ComponentProviderAdapter is a class that extends the ComponentProvider class such that a GUI component can be properly added. You have to create a subclass of this class to implement the functionality and the GUI for your plugin. For its GUI, Ghidra makes use of the javax.swing library and all of its swing components. Thus, you have to override the constructor to create the right GUI components. You also need to override the getComponent() method to return the right GUI component that you want to display. Here is a simple example:
```python
class SimpleComponentProviderAdapter(ComponentProviderAdapter):
    def __init__(self, tool, name):
        #Call default constructor with plugin name and the current PluginTool object
        ComponentProviderAdapter.__init__(self, tool, name, name)
        #Create an editable javax.swing textarea
        self.textArea = JTextArea(10, 80)
        self.textArea.setEditable(True)
        self.textArea.setLineWrap(True)
        #Set the position of the component to the right
        self.setDefaultWindowPosition(WindowPosition.RIGHT)
        #Set title of component
        self.setTitle("OpenAI Pseudocode")
        #Set component to be visible
        self.setVisible(True)

    def getComponent(self):
        return self.textArea
```
## [DockingAction](https://ghidra.re/ghidra_docs/api/docking/action/DockingAction.html)
The DockingAction is a class that represents the action associated with a particular menu or toolbar item. You can create a subclass of the DockingAction superclass and then define your own custom action or menu item. An instance of this subclass can be then added to a ComponentProviderAdapter object. In the DockingAction subclass, you must override the actionPerformed method which defines the code that will run when the menu item is triggered. You can associate an icon and keybinding with particular DockingAction objects. Here is a simple example:
```python
class SimpleDockingAction(DockingAction):
def __init__(self, owner):
        #Pass owner and tooltip to superclass constructor
        DockingAction.__init__(self, "Tooltip for action", owner, False)
        self.markHelpUnnecessary()
        #Enable the DockingAction
        self.setEnabled(True)
        #Load and set an icon for the DockingAction
        icon = ResourceManager.loadImage("images/edit-cut.png")
        self.setToolBarData(ToolBarData(icon))

    #Override the actionPerformed method
    def actionPerformed(self, actionContext):
        print("Overridden!")
```
## Conclusion
With this information, you should now be able to create GUI components for your plugin. For more complex GUI components and styles, all you have to do is to modify the java swing code inside the overridden ComponentProviderAdapter class.
