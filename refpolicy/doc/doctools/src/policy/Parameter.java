/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Parameter.java: The reference policy interface parameters
 * Version: @version@ 
 */
package policy;
 
/**
 * Each reference policy layer is represented by this class.
 * 
 * @see Layer
 * @see Module
 * @see Interface
 */
public class Parameter extends PolicyElement{
	
	/**
	 * Default constructor assigns name to parameter.
	 * 
	 * @param _name		The name of the parameter.
	 * @param _Parent 	The reference to the parent element.
	 */
	public Parameter(String _name, Interface _Parent){
		super(_name, _Parent);
	}
}