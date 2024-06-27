package jparser;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.expr.SimpleName;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class JavaVariableParser {

    public static List<String> findVariableNameRangeByLineNumber(String filePath, String variableName, int lineNumber) {
        try {
            CompilationUnit cu = StaticJavaParser.parse(new File(filePath));

            // Custom visitor to find the variable name with specific line number
            VariableNameRangeFinder finder = new VariableNameRangeFinder(variableName, lineNumber);
            finder.visit(cu, null);

            return finder.getVariableNameRange();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return null;
    }

    private static class VariableNameRangeFinder extends VoidVisitorAdapter<Object> {
        private final String variableName;
        private final int lineNumber;
        private String variableNameRange;
        List<String> variableNameRanges = new ArrayList<String>(); 

        public VariableNameRangeFinder(String variableName, int lineNumber) {
            this.variableName = variableName;
            this.lineNumber = lineNumber;
        }

        public List<String> getVariableNameRange() {
            return variableNameRanges;
        }

        @Override
        public void visit(SimpleName sn, Object arg) {
            super.visit(sn, arg);
            if (sn.asString().equals(variableName)) {
                Optional<com.github.javaparser.Range> range = sn.getRange();
                if (range.isPresent() && range.get().begin.line == lineNumber) {
                    variableNameRange = range.get().begin.line + ", " +
                                        range.get().begin.column + ", " +
                                        range.get().end.line + ", " +
                                        range.get().end.column;
                    variableNameRanges.add("["+variableNameRange+"]");
                }
            }
        }
    }
}



