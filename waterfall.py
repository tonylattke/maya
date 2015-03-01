import sys
import random
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaFX as OpenMayaFX
import maya.cmds as cmds

commandName = 'waterfall'

class Waterfall(OpenMayaMPx.MPxCommand):
	
	# Contador de numero de instancias
	instanceId = 0
	
	# Valores por defecto
	default_numTurbulence	= 3
	default_dewRate  		= 100
	default_spumeRate		= 100
	default_waterRate		= 100
	default_floor			= -20
	default_turbulence_low	= 5
	default_turbulence_high	= 50
	
	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)
		
		# Asignando un nombre unico a la instancia
		self.instanceName = commandName + str(Waterfall.instanceId)
		Waterfall.instanceId += 1
		
		# Nombres de sistema de particulas de gotas, espuma y agua
		self.dewSystemName 		= self.instanceName + '_Dew'
		self.spumeSystemName 	= self.instanceName + '_Spume'
		self.waterSystemName 	= self.instanceName + '_water'

		self.dewSystemShapeName   = self.dewSystemName + 'Shape'
		self.spumeSystemShapeName = self.spumeSystemName + 'Shape'
		self.waterSystemShapeName = self.waterSystemName + 'Shape'

		# Nombres de emisores de particulas de gotas, espuma y agua
		self.dewEmitterName 	= self.instanceName + '_DewEmiter'
		self.spumeEmitterName 	= self.instanceName + '_SpumeEmiter'
		self.waterEmitterName 	= self.instanceName + '_WaterEmiter'

		# Campos de fuerzas
		self.gravityName 		= self.instanceName + '_Gravity'
		self.turbulenceLowName 	= self.instanceName + '_TurbulenceLow'
		self.turbulenceHighName	= self.instanceName + '_TurbulenceHigh'

		# Values
		self.numTurbulence 		= Waterfall.default_numTurbulence
		self.dewRate 			= Waterfall.default_dewRate
		self.spumeRate 			= Waterfall.default_spumeRate
		self.waterRate 			= Waterfall.default_waterRate
		self.floor 				= Waterfall.default_floor
		self.turbulenceLow 		= Waterfall.default_turbulence_low
		self.turbulenceHigh		= Waterfall.default_turbulence_high

		# Control
		self.controllerName		= self.instanceName + '_Control'		

		self.dagModifier		= OpenMaya.MDagModifier()
	
	def isUndoable(self):
		return True
	
	def parseArgs(self, args):
		argData = OpenMaya.MArgParser(self.syntax(), args)
		
		if (argData.isFlagSet('nt')):
			self.numTurbulence = argData.flagArgumentInt('nt', 0)
		
		if (argData.isFlagSet('dr')):
			self.dewRate = argData.flagArgumentInt('dr', 0)

		if (argData.isFlagSet('sr')):
			self.spumeRate = argData.flagArgumentInt('sr', 0)

		if (argData.isFlagSet('wr')):
			self.waterRate = argData.flagArgumentInt('wr', 0)
		
		if (argData.isFlagSet('f')):
			self.waterRate = argData.flagArgumentDouble('f', 0)
		if (argData.isFlagSet('tl')):
			self.turbulenceLow = argData.flagArgumentDouble('f', 0)
		if (argData.isFlagSet('th')):
			self.turbulenceHigh = argData.flagArgumentDouble('f', 0)
	
	def doIt(self, args):
		# Procesar argumentos
		try:
			self.parseArgs(args)
		except Exception as e:
			print('[' + commandName + '] Sintaxis de flag invalida' )
			return
		
		# Guardar seleccion de la superficie
		surface = cmds.ls( sl=True)
		
		# Crear el control maestro
		cmds.spaceLocator(name=self.controllerName)
		cmds.addAttr(ln='floor',at='double',defaultValue=self.floor)
		cmds.addAttr(ln='beginTolerance',at='double',defaultValue=0.3)
		cmds.addAttr(ln='magnitudeTLow',at='double',defaultValue=self.turbulenceLow)
		cmds.addAttr(ln='magnitudeTHigh',at='double',defaultValue=self.turbulenceHigh)

		OpenMaya.MGlobal.clearSelectionList()
		cmds.gravity(name=self.gravityName,m=9.8,att=0,dx=0,dy=-1,dz=0)
		OpenMaya.MGlobal.clearSelectionList()
		cmds.turbulence(name=self.turbulenceHighName,att=0)
		OpenMaya.MGlobal.clearSelectionList()
		cmds.turbulence(name=self.turbulenceLowName,att=0)

		cmds.expression(s="phaseX = time*135.165;\nphaseY = time+10*135.165;\nphaseZ = time+767*135.165;",o=self.turbulenceHighName,alwaysEvaluate=1)
		
		cmds.connectAttr(self.controllerName + '.magnitudeTLow', self.turbulenceLowName + '.magnitude')
		cmds.connectAttr(self.controllerName + '.magnitudeTHigh', self.turbulenceHighName + '.magnitude')

		##################################### Gotas #####################################
		# Crear sistema y emisor
		cmds.select(surface)

		cmds.emitter(n=self.dewEmitterName, type='surface',rate=self.dewRate)
		cmds.particle(n=self.dewSystemName)
		cmds.connectDynamic(self.dewSystemShapeName, em=self.dewEmitterName)

		# Agregar goal entre superficie y sistema
		cmds.select(self.dewSystemName, r=True)
		cmds.select(surface, add=True )
		cmds.goal(self.dewSystemName, g=surface, w=1, utr=0)

		cmds.connectDynamic(self.dewSystemName, f=self.gravityName)
		cmds.connectDynamic(self.dewSystemName, f=self.turbulenceLowName)
		cmds.connectDynamic(self.dewSystemName, f=self.turbulenceHighName)

		# Setear valores
		cmds.setAttr(self.dewSystemShapeName+".conserve",0.98);
		cmds.setAttr(self.dewSystemShapeName+".lifespanMode",3); # only LifespanPP
		cmds.setAttr(self.dewSystemShapeName+".particleRenderType",3); # points
		cmds.select(self.dewSystemShapeName)
		cmds.addAttr(ln='goalU', dt='doubleArray');
		cmds.addAttr(ln='goalU0', dt='doubleArray');
		cmds.addAttr(ln='goalV', dt='doubleArray');
		cmds.addAttr(ln='goalV0', dt='doubleArray');
		cmds.addAttr(ln='opacityPP', dt='doubleArray');
		cmds.addAttr(ln='opacityPP0', dt='doubleArray');
		cmds.dynExpression(self.dewSystemShapeName, s="goalV = 0;\ngoalU = rand(1);\ngoalPP = rand(0.7,1);\nopacityPP = 0;",c=1)
		cmds.dynExpression(self.dewSystemShapeName, s="goalV += rand(0.1);\nif (goalV > " + self.controllerName + ".beginTolerance){\n\topacityPP = 1;\n}\nif (goalV > 0.99){\n\tgoalPP = 0;\n\tvector $pos = position;\n\tif ($pos.y < " + self.controllerName + ".floor){\n\t\tlifespanPP = 0;\n\t}\n};",rbd=1)

		# cmds.select(surface)
		# cmds.emitter(n=self.spumeEmitterName, type='surface')
		# cmds.particle(n=self.spumeSystemName)
		# cmds.connectDynamic(self.spumeSystemShapeName, em=self.spumeEmitterName)

		# cmds.select(surface)
		# cmds.emitter(n=self.waterEmitterName, type='surface')
		# cmds.particle(n=self.waterSystemName)
		# cmds.connectDynamic(self.waterSystemShapeName, em=self.waterEmitterName)
		self.dagModifier.doIt()
	
	def redoIt(self):
		self.dagModifier.doIt()
	
	def undoIt(self):
		self.dagModifier.undoIt()
	
	def getDagPathToObject(self, objectName):
		selectionList = OpenMaya.MSelectionList()
		OpenMaya.MGlobal.getSelectionListByName(objectName,selectionList)
		dagPath = OpenMaya.MDagPath()
		selectionList.getDagPath(0,dagPath)
		return dagPath

# Retorna una instancia del comando
def cmdCreator():
	return OpenMayaMPx.asMPxPtr(Waterfall())

def syntaxCreator():
	# Crea una instancia de MSyntax con la sintaxis que querramos
	syntax = OpenMaya.MSyntax()
	
	# Agregando los flags
	syntax.addFlag('nt', 'numTurbulence', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('dr', 'dewRate', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('sr', 'spumeRate', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('wr', 'waterRate', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('f' , 'floor', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('tl' , 'turbulenceLow', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('th' , 'turbulenceHigh', OpenMaya.MSyntax.kDouble)
	
	return syntax
	
def initializePlugin(mObject):
	plugin = OpenMayaMPx.MFnPlugin(mObject)
	try:
		plugin.registerCommand(commandName, cmdCreator, syntaxCreator)
	except:
		sys.stderr.write('Fallo al registrar el commando: ' + commandName)

def uninitializePlugin(mObject):
	plugin = OpenMayaMPx.MFnPlugin(mObject)
	try:
		plugin.deregisterCommand(commandName)
	except:
		sys.stderr.write('Fallo al registrar el commando: ' + commandName)
		
# Uso

'''
import maya.cmds as cmds

cmds.flushUndo()

cmds.waterfall()

cmds.waterfall(np=100, dim=(3,5,2))
'''