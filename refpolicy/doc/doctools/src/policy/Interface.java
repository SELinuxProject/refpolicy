/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Interface.java: The reference policy interfaces
 * Version: @version@ 
 */
package policy;

import java.util.Map;
import java.util.TreeMap;
 
/**
 * Each reference policy interface is represented by this class.
 * 
 * @see Layer
 * @see Module
 * @see Parameter
 */
public class Interface extends PolicyElement {
	/** the children of this element */
	public final Map<String,Parameter> Children;

	public InterfaceType Type;
	public int Weight;
	
	/**
	 * Default constructor assigns name to module.
	 * 
	 * @param _name		The name of the module.
	 * @param _Parent 	The reference to the parent element.
	 */
	public Interface(String _name, Module _Parent){
		super(_name, _Parent);
		Children = new TreeMap<String,Parameter>();
	}	
}