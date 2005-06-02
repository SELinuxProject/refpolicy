/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Policy.java: The reference policy api		
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
public class Policy extends PolicyElement {
	/** the children of this element */
	public final Map<String,Layer> Children;
	
	/**
	 * Default constructor assigns name to layer.
	 * 
	 * @param _name		The name of the layer.
	 * @param _Parent 	The reference to the parent element.
	 */
	public Policy(String _name){
		// the policy is the root element so parent==null
		super(_name, null);
		Children = new TreeMap<String,Layer>();
	}	
}