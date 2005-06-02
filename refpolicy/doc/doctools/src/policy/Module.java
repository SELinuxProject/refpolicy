/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Module.java: The reference policy module		
 * Version: @version@ 
 */
package policy;

import java.util.Map;
import java.util.TreeMap;

/**
 * Each reference policy layer is represented by this class.
 * 
 * @see Layer
 * @see Interface
 * @see Parameter
 */
public class Module extends PolicyElement {
	/** the children of this element */
	public final Map<String,Interface> Children;
		
	/**
	 * Default constructor assigns name to module.
	 * 
	 * @param _name		The name of the module.
	 * @param _Parent 	The reference to the parent element.
	 */
	public Module(String _name, Layer _Parent){
		super(_name, _Parent);
		Children = new TreeMap<String,Interface>();
	}
}