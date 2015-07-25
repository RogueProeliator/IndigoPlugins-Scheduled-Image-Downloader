#! /usr/bin/env python
# -*- coding: utf-8 -*-
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# Scheduled Image Downloader by RogueProeliator <rp@rogueproeliator.com>
# 	See plugin.py for more plugin details and information
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////

#/////////////////////////////////////////////////////////////////////////////////////////
# Python imports
#/////////////////////////////////////////////////////////////////////////////////////////
from urlparse import urlparse
import indigo
import RPFramework

#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
# SonyTvNetworkRemoteDevice
#	Handles the configuration of a single Sony device that is connected to this plugin;
#	this class does all the 'grunt work' of communications with the device
#/////////////////////////////////////////////////////////////////////////////////////////
#/////////////////////////////////////////////////////////////////////////////////////////
class ScheduledImageDownloadDevice(RPFramework.RPFrameworkRESTfulDevice.RPFrameworkRESTfulDevice):
	
	#/////////////////////////////////////////////////////////////////////////////////////
	# Class construction and destruction methods
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# Constructor called once upon plugin class receiving a command to start device
	# communication. The plugin will call other commands when needed, simply zero out the
	# member variables
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def __init__(self, plugin, device):
		super(ScheduledImageDownloadDevice, self).__init__(plugin, device)
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should return the HTTP address that will be used to connect to the
	# RESTful device. It may connect via IP address or a host name
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def getRESTfulDeviceAddress(self):
		# obtain the defaults...
		urlPattern = self.indigoDevice.pluginProps.get("urlPattern", "")
		hostName = ""
		portNumber = 80
		
		# determine the host and port from the pattern, if we are able...
		if urlPattern != "":
			parsedUrl = urlparse(urlPattern)
			hostName = parsedUrl.netloc
			try:
				if not (parsedUrl is None):
					portNumber = parsedUrl.port
			except:
				portNumber = 80
		
		# return our results...
		return (hostName, portNumber)
		
	
	#/////////////////////////////////////////////////////////////////////////////////////
	# Processing and command functions
	#/////////////////////////////////////////////////////////////////////////////////////
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine should be overridden in individual device classes whenever they must
	# handle custom commands that are not already defined
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	def handleUnmanagedCommandInQueue(self, deviceHTTPAddress, rpCommand):
		if rpCommand.commandName == "PROCESS_IMAGE_DOWNLOAD":
			# this command should "expand" the URL and queue up file downloads to be
			# processed individually (in the case of a patterned usage)
			
			# check to see if this URL has a pattern or is a fully-qualified (single) url
			imageUrl = self.indigoDevice.pluginProps.get("urlPattern", "")
			savePath = self.indigoDevice.pluginProps.get("saveFilename", "")
			authenticationMethod = self.indigoDevice.pluginProps.get("authenticationType", "none")
			username = self.indigoDevice.pluginProps.get("urlUsername", "")
			password = self.indigoDevice.pluginProps.get("urlPassword", "")
			if imageUrl == "":
				return
			elif imageUrl.find("%d") == -1:
				# this is a straight URL download, queue the file for download now...
				self.hostPlugin.logDebugMessage("Creating command to download " + imageUrl + " to " + savePath, RPFramework.RPFrameworkPlugin.DEBUGLEVEL_HIGH)
				self.queueDeviceCommand(RPFramework.RPFrameworkCommand.RPFrameworkCommand(RPFramework.RPFrameworkRESTfulDevice.CMD_DOWNLOADFILE, commandPayload=(imageUrl, savePath, authenticationMethod, username, password)))
			else:
				# this is a pattern-URL that we need to do substitution on...
				beginIdx = int(self.indigoDevice.pluginProps.get("patternStartNumber", "0"))
				endIdx = int(self.indigoDevice.pluginProps.get("patternEndNumber", "0"))
				patternDownloadFileDelay = float(self.indigoDevice.pluginProps.get("patternCommandDelay", "0.1"))
				
				if beginIdx > endIdx:
					indigo.server.log("Invalid pattern provided - the ending index occurs before the beginning index.", isError=True)
				else:
					commandsToQueue = []
					tempIdx = beginIdx
					while tempIdx <= endIdx:
						patternReplacedUrl = imageUrl % tempIdx
						patternReplacedSave = savePath % tempIdx
						commandsToQueue.append(RPFramework.RPFrameworkCommand.RPFrameworkCommand(RPFramework.RPFrameworkRESTfulDevice.CMD_DOWNLOADFILE, commandPayload=(patternReplacedUrl, patternReplacedSave, authenticationMethod, username, password), postCommandPause=patternDownloadFileDelay))
						tempIdx = tempIdx + 1
					self.queueDeviceCommands(commandsToQueue)
			
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
	# This routine will handle an error as thrown by the REST call... it allows 
	# descendant classes to do their own processing
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-		
	def handleRESTfulError(self, rpCommand, err):
		if rpCommand.commandName == RPFramework.RPFrameworkRESTfulDevice.CMD_DOWNLOADFILE:
			self.indigoDevice.updateStateOnServer("downloadStatus", value="False", uiValue="Error")
			self.indigoDevice.setErrorStateOnServer("Download Failed")
	