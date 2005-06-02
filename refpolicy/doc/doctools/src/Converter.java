/* Copyright (C) 2005 Tresys Technology, LLC
 * License: refer to COPYING file for license information.
 * Authors: Spencer Shimko <sshimko@tresys.com>
 * 
 * Converter.java: The reference policy documentation converter		
 * Version: @version@ 
 */
import policy.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintStream;

import java.util.Map;

/**
 * The reference policy documentation generator and xml analyzer class.
 * It pulls in XML describing reference policy, transmogrifies it,
 * and spits it back out in some other arbitrary format.
 */
public class Converter{
	private Policy policy;
	private static final String HTMLEXT = ".html";
	private static final String indexContent = 
		"<div id=\"Content\"><h2>Welcome to the reference policy API!</h2><p/>" +
		"Please choose from the navigation options to the left.</div>";

	private StringBuffer headerOutput = new StringBuffer();
	private StringBuffer footerOutput = new StringBuffer();
	private File outDir;
	
	public Converter(Policy pol, File headerFile, File footerFile) throws IOException{
		policy = pol;

		/*
		 * Setup header and footer. 
		 */
		FileReader headIn = new FileReader(headerFile);

		BufferedReader br = new BufferedReader(headIn);
	    String line = null; //not declared within while loop
	    while (( line = br.readLine()) != null){
	        headerOutput.append(line);
	        headerOutput.append(System.getProperty("line.separator"));
	    }
		
		FileReader footerIn = new FileReader(footerFile);
				
		br = new BufferedReader(footerIn);
	    line = null; //not declared within while loop
	    while (( line = br.readLine()) != null){
	        footerOutput.append(line);
	        footerOutput.append(System.getProperty("line.separator"));
	    }
	}
	
	public void Convert(File _outDir) throws IOException{
		outDir = _outDir;

		// write the index document
		FileWrite("index" + HTMLEXT, headerOutput.toString() 
				+ Menu().toString() + indexContent + footerOutput.toString());
		
		// walk the policy and write pages for each module
		for(Map.Entry<String,Layer> lay:policy.Children.entrySet()){
			Layer layer = lay.getValue();
			// the base output contains the menu and layer content header
			StringBuffer baseOutput = new StringBuffer();
			// the layer output will be filled with modules and summarys for content
			StringBuffer layerOutput = new StringBuffer();
			
			// create the navigation menu
			baseOutput.append(Menu(layer.Name));

			baseOutput.append("<div id=\"Content\">\n");
			baseOutput.append("\t<h1>Layer: " + layer.Name + "</h1><p/>\n");
		
			layerOutput.append("<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\" width=\"75%\">\n");
			layerOutput.append("<tr><th class=\"title\">Module&nbsp;Name</th>" + 
					"<th class=\"title\">Summary</th></tr>");
			
			for(Map.Entry<String,Module> mod:layer.Children.entrySet()){
				// module output will be filled with in-depth module info.
				StringBuffer moduleOutput = new StringBuffer();
				Module module = mod.getValue();
				
				// get the content for the module's document
				moduleOutput.append(moduleContent(mod.getValue()).toString() + "</div>");
				
				// get the summary and name for the layer's document

				layerOutput.append("<tr><td><a href=\"" + layer.Name + "_" + module.Name + HTMLEXT 
						+ "\">" + module.Name + "</a></td>" +
						"\n<td>" + module.PCDATA + "</td></tr>\n");
				
				// write module document
				FileWrite(layer.Name + "_" + module.Name + HTMLEXT, 
					headerOutput.toString() + "\n" + baseOutput.toString() + moduleOutput.toString() + footerOutput.toString());
			}
			// write layer document
			FileWrite(layer.Name + HTMLEXT, 
				headerOutput.toString() + "\n" + baseOutput.toString() 
				+ layerOutput.toString() + "</div>" + footerOutput.toString());

		}
	}
	
	private StringBuffer Menu(String key){
		StringBuffer out = new StringBuffer();
		out.append("<div id=\"Menu\">\n");
		for(Map.Entry<String,Layer> layer:policy.Children.entrySet()){
			String layerName = layer.getKey();
			
			
			// show the modules for the current key
			if (layerName.equals(key)){
				out.append("\t<a href=\"" + layerName 
						+ HTMLEXT + "\">" + layerName + "</a><br />\n");
				out.append("\t<div id=\"subitem\">\n");
				for(Map.Entry<String,Module> module:layer.getValue().Children.entrySet()){
					String moduleName = module.getKey();
					out.append("\t\t-&nbsp;<a href=\"" + layerName + "_" + moduleName + HTMLEXT 
							+ "\">" + moduleName + "</a><br />\n");
				}
				out.append("\t</div>\n");
			} else {
				out.append("\t<a href=\"" + layerName +
						HTMLEXT + "\">+&nbsp;" + layerName + "</a><br />\n");
			}
		}
		out.append("</div>");
		return out;
	}

	private StringBuffer Menu(){
		StringBuffer out = new StringBuffer();
		out.append("<div id=\"Menu\">\n");
		for(Map.Entry<String,Layer> layer:policy.Children.entrySet()){
			String layerName = layer.getKey();
			
			
			out.append("\t<a href=\"" + layerName + HTMLEXT + "\">" + layerName + "</a><br />\n");
			out.append("\t<div id=\"subitem\">\n");
			for(Map.Entry<String,Module> module:layer.getValue().Children.entrySet()){
				String moduleName = module.getKey();
				out.append("\t\t-&nbsp;<a href=\"" + layerName + "_" + moduleName + HTMLEXT 
						+ "\">" + moduleName + "</a><br />\n");
			}
			out.append("\t</div>\n");
		}
		out.append("</div>");
		return out;
	}

	private StringBuffer moduleContent(Module module){
		StringBuffer out = new StringBuffer();

		out.append("\t<h2>Module:&nbsp;"+ module.Name + "<br />\n");
		out.append("\tSummary:&nbsp;" + module.PCDATA + "</h2>\n");
		for (Map.Entry<String,Interface> inter:module.Children.entrySet()){
			Interface iface = inter.getValue();
			// main table header
			out.append("<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\" width=\"75%\">\n");
			out.append("<tr><th class=\"title\" colspan=\"3\">Interface</th></tr>\n");
			
			// only show weight when type isnt none
			if (iface.Type != InterfaceType.None){
				out.append("<tr><td>Name</td><td colspan=\"2\">" + iface.Name + "</td></tr>\n" +
						"<tr><td>Flow&nbsp;Type</td><td colspan=\"2\">" + iface.Type.toString() + "</td></tr>\n");
				out.append("\t<td>Flow&nbsp;Weight</td><td colspan=\"2\">" + iface.Weight + "</td></tr>\n");
			} else {
				out.append("<tr><td>Name</td><td colspan=\"2\">" + iface.Name + "</td></tr>\n");
				out.append("<tr><td>Flow&nbsp;Type</td><td colspan=\"2\">" + iface.Type.toString() + "</td></tr>\n");
				
			}
			out.append("<tr><td>Description</td><td colspan=\"2\">" + iface.PCDATA + "</td></tr>\n");
			
			out.append("<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\" width=\"75%\">\n" 
					+ "<tr><th class=\"title\">Parameter</th><th class=\"title\">Description</th>" 
					+ "<th class=\"title\">Optional</th></tr>");
			for (Map.Entry<String,Parameter> param:iface.Children.entrySet()){
				Parameter parameter = param.getValue();
				out.append("\t<tr><td> " + parameter.Name + "</td>\n");
				out.append("\t<td>" + parameter.PCDATA + "</td>\n");
				String opt = parameter.GetAttribute("optional");
				if (opt != null && opt.equalsIgnoreCase("true")){
					out.append("\t<td><center>Yes</center></td></tr>\n");
				} else {
					out.append("\t<td><center>No</center></td></tr>\n");
				}
			}
			out.append("\n</table></table><br/><br/>\n");
		}
		return out;
	}
	
	/**
	 * Write to sub directory.
	 * @param path
	 * @param outFilename
	 * @param content
	 * @return
	 */
	private void FileWrite (String path, String outFilename, String content){
		try {
			// create parent if necessary
			File outParent = new File(outDir, path );
			File outFile = new File(outParent, outFilename );
			if (outParent.exists() && !outParent.isDirectory()){
				throw new IOException("Output directory not really a directory");
			} else if (!outParent.exists()){
				outParent.mkdirs();
			} 
			PrintStream stream = new PrintStream(new FileOutputStream(outFile));
			stream.println(content);
			stream.flush();
			stream.close();
		} catch (Exception e){
			System.err.println (e.getMessage());
			System.exit(1);
		}
	}
	
	/**
	 * Write to output directory directly.
	 * 
	 * @param path
	 * @param outFilename
	 * @param content
	 * @return
	 */
	private void FileWrite (String outFilename, String content){
		try {
			File out = new File(outDir, outFilename );
			PrintStream stream = new PrintStream(new FileOutputStream(out));
			stream.println(content);
			stream.flush();
			stream.close();
		} catch (Exception e){
			System.err.println (e.getMessage());
			System.exit(1);
		}
	}
}