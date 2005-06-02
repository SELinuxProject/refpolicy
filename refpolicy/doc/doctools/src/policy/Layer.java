/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Layer.java: The reference policy layers		
 * Version: @version@ 
 */
package policy;

import java.util.Map;
import java.util.TreeMap;

/**
 * Each reference policy layer is represented by this class.
 * 
 * @see Module
 * @see Interface
 * @see Parameter
 */
public class Layer extends PolicyElement {
	/** the children of this element */
	public final Map<String,Module> Children;
	
	/**
	 * Default constructor assigns name to layer.
	 * 
	 * @param _name		The name of the layer.
	 * @param _Parent 	The reference to the parent element.
	 */
	public Layer(String _name, Policy _Parent){
		super(_name, _Parent);
		Children = new TreeMap<String, Module>();
	}
}