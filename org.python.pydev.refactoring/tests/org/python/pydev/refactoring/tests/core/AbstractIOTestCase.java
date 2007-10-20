/* 
 * Copyright (C) 2006, 2007  Dennis Hunziker, Ueli Kistler 
 */

package org.python.pydev.refactoring.tests.core;

import java.io.File;

import junit.framework.TestCase;

import org.python.pydev.refactoring.ast.PythonModuleManager;

/**
 * @author Dennis Hunziker, Ueli Kistler
 */
public abstract class AbstractIOTestCase extends TestCase implements IInputOutputTestCase {

	private static final String EMPTY = "";

	private StringBuffer sourceLines = null;

	private StringBuffer resultLines = null;

	private StringBuffer configLines;

	private String generated;
	
	private File file;

	public AbstractIOTestCase(String name) {
		this(name, false);
	}

	@Override
	protected void setUp() throws Exception {
		PythonModuleManager.TESTING = true;
	}
	
	@Override
	protected void tearDown() throws Exception {
		PythonModuleManager.TESTING = false;
	}
	
	public AbstractIOTestCase(String name, boolean ignoreEmptyLines) {
		super(name);
		sourceLines = new StringBuffer();
		resultLines = new StringBuffer();
		configLines = new StringBuffer();
	}

	public String getExpected() {
		return EMPTY.equals(getResult()) ? getSource() : getResult();
	}

	public String getResult() {
		return getResultLines().toString().trim();
	}

	public String getSource() {
		return getSourceLines().toString().trim();
	}

	public void setSource(String line) {
		sourceLines.append(line);
	}

	public void setResult(String line) {
		resultLines.append(line);
	}

	public void setConfig(String line) {
		configLines.append(line);
	}

	private StringBuffer getResultLines() {
		return resultLines;
	}

	protected String getGenerated() {
		return generated.trim();
	}

	protected String getConfig() {
		return configLines.toString().trim();
	}

	private StringBuffer getSourceLines() {
		return sourceLines;
	}

	public void setTestGenerated(String source) {
		this.generated = source;
	}

	public void setFile(File file) {
		this.file = file;
	}

	public File getFile() {
		return file;
	}
}
