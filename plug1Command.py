import sys
import random
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaFX as OpenMayaFX

commandName = 'plug1'

class Plug1Command(OpenMayaMPx.MPxCommand):
	
	# Contador de numero de instancias
	instanceId = 0
	
	# Valores por defecto
	default_numParticles = 50
	default_dimmensions  = (5 , 5, 5)
	
	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)
		
		# Asignando un nombre unico a la instancia
		self.instanceName = commandName + str(Plug1Command.instanceId)
		Plug1Command.instanceId += 1
		
		# Instanciando variables al sistema de particulas
		self.particleSystemName = self.instanceName + '_Particles'
		self.numParticles		= Plug1Command.default_numParticles
		self.particlesPositions	= OpenMaya.MPointArray()
		
		# Instanciando variables al campo de turbulencia
		self.turbulenceFieldName= self.instanceName + '_Turbulence'
		self.size_x 			= Plug1Command.default_dimmensions[0]
		self.size_y 			= Plug1Command.default_dimmensions[1]
		self.size_z 			= Plug1Command.default_dimmensions[2]
		
		self.dagModifier		= OpenMaya.MDagModifier()
	
	def isUndoable(self):
		return True
	
	def parseArgs(self, args):
		argData = OpenMaya.MArgParser(self.syntax(), args)
		
		if (argData.isFlagSet('np')):
			self.numParticles = argData.flagArgumentInt('np', 0)
		
		if (argData.isFlagSet('dim')):
			self.size_x = argData.flagArgumentDouble('dim', 0)
			self.size_y = argData.flagArgumentDouble('dim', 1)
			self.size_z = argData.flagArgumentDouble('dim', 2)
			
	
	def doIt(self, args):
		# Procesar argumentos
		try:
			self.parseArgs(args)
		except Exception as e:
			print('[' + commandName + '] Sintaxis de flag invalida' )
			return
			
		# Deseleciona todo
		OpenMaya.MGlobal.clearSelectionList()
		
		# Crea el campo de turbulencia
		self.dagModifier.commandToExecute('turbulence -name "' + self.turbulenceFieldName + '"')
		self.dagModifier.commandToExecute('scale ' + str(0.5 * self.size_x) + ' '
												   + str(0.5 * self.size_y) + ' '
												   + str(0.5 * self.size_z) + ' '
												   + self.turbulenceFieldName)
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.volumeShape" 1') # 1 para cubo, 2 para esfera
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.magnitude" 100')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.attenuation" 0.1')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.frequency" 4')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.interpolationType" 1')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.noiseLevel" 8')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.noiseRatio" 1')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.trapInside" 1')
		self.dagModifier.commandToExecute('setAttr "' + self.turbulenceFieldName + '.trapRadius" 1')
		
		# Crea el sistema de particulas
		self.dagModifier.commandToExecute('particle -name "' + self.particleSystemName + '"')
		self.dagModifier.commandToExecute('setAttr "' + self.particleSystemName + 'Shape.conserve" 0.75')
		self.dagModifier.commandToExecute('setAttr "' + self.particleSystemName + 'Shape.particleRenderType" 6') # 3 para puntos, 6 para streaks
		
		# Conecta el sistema de particulas con el campo de fuerza
		self.dagModifier.commandToExecute('connectDynamic -f ' + self.turbulenceFieldName + ' ' + self.particleSystemName + 'Shape')
		
		# Ejecuta los comandos encolados
		self.dagModifier.doIt()
		
		
		# Ayuda a obtener el Dag path del particleShape
		particleShapeDagPath = self.getDagPathToObject(self.particleSystemName + 'Shape')
		
		# Crea una funcion para establecer al particleShapeDagPath
		particleSystemFn = OpenMayaFX.MFnParticleSystem(particleShapeDagPath)
		
		# Genera aleatoriamente las posiciones de las particulas
		for i in range(0, self.numParticles):
			self.particlesPositions.append(random.uniform(0.5 * -self.size_x, 0.5 * self.size_x), 
										  random.uniform(0.5 * -self.size_y, 0.5 * self.size_y),
										  random.uniform(0.5 * -self.size_z, 0.5 * self.size_z))
		
		# Emite particulas usando las posiciones generadas
		particleSystemFn.emit(self.particlesPositions)
		
		particleSystemFn.saveInitialState()
	
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
	return OpenMayaMPx.asMPxPtr(Plug1Command())

def syntaxCreator():
	# Crea una instancia de MSyntax con la sintaxis que querramos
	syntax = OpenMaya.MSyntax()
	
	# Agregando los flags
	syntax.addFlag('np', 'numParticles', OpenMaya.MSyntax.kDouble)
	syntax.addFlag('dim', 'dimensions', OpenMaya.MSyntax.kDouble, OpenMaya.MSyntax.kDouble, OpenMaya.MSyntax.kDouble)
	
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

cmds.plug1()

cmds.plug1(np=100, dim=(3,5,2))
'''