/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * PolicyElement.java: The reference policy base class		
 * Version: @version@ 
 */
package policy;

import java.util.Map;
import java.util.TreeMap;

/**
 * Reference policy elements have certain similarties which
 * should be inherited from a base class.  This includes a name
 * attribute that will be used for hashing, sorting, and converting
 * to a string.  
 * 
 * @see Layer
 * @see Module
 * @see Interface
 * @see Parameter
 */
public abstract class PolicyElement {
	/** the string identifying the element */
	public final String Name;
	/** the parent component */
	public final PolicyElement Parent;

	/** the attributes of this element */
	private final Map<String,String> attributes;
	
	public String PCDATA;

	/**
	 * Default constructor assigns name.
	 * 
	 * @param _name		The name of the element.
	 * @param _Parent 	The reference to the parent element.
	 */
	public PolicyElement(String _name, PolicyElement _Parent){
		Name = _name;
		Parent = _Parent;
		attributes = new TreeMap<String,String>();
	}
	
	/**
	 * Add attribute to policy element.
	 * 
	 * @param aName		String to identify attribute
	 * @param aString 	Value of attribute identified by string aName
	 * @return 			<code>true</code> when attribute added to element,
	 * 					<code>false</code> when attribute already defined for element 
	 */
	public boolean AddAttribute(String aName, String aString){
		if (attributes.containsKey(aName)){
			return false;
		}
		attributes.put(aName,aString);
		return true;
	}
	
	/**
	 * Get attribute from policy element.
	 * 
	 * @param aName		String to identify attribute
	 * @return 			String value associated with named attribute
	 * 					or <code>null</code> if no attribute defined
	 * 					for aName. 
	 */
	public String GetAttribute(String aName){
		return attributes.get(aName);
	}

	/**
	 * Overridden equals method
	 * 
	 * @param obj	Object for comparison
	 */
	@Override public boolean equals(Object obj){
		return obj.toString().equals(this.Name);
	}

	/**
	 * Return a hashcode for the element. Currently implemented as a 
	 * call to the String hashCode() method.
	 * 
	 * @return integer hashCode of this instance assuring two objects that
	 * 		   are == will return same hashcode.
	 */
	@Override public int hashCode() {
		return this.toString().hashCode();
	}
	
	/**
	 * Overridden toString() method.
	 * 
	 * @return String representation of instance (it's name).
	 */
	@Override public String toString(){
			return Name;
	}		
	
	/**
	 * Since Component might be used as a key in some type of sort Compare
	 * is implemented.
	 * 
	 * @return	0 if this==that, <0 if this<that, >0 if this>that
	 * @see String.compareTo
	 */
	public int compareTo(Layer that){
		return Name.compareTo(that.Name);
	}
}