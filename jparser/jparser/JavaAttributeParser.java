package jparser;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Optional;

public class JavaAttributeParser {

    public static String findAttributeNameRangeByLineNumber(String filePath, String attributeName, int lineNumber) {
        try {
            CompilationUnit cu = StaticJavaParser.parse(new File(filePath));

            AttributeNameRangeFinder finder = new AttributeNameRangeFinder(attributeName, lineNumber);
            finder.visit(cu, null);

            return finder.getAttributeNameRange();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return null;
    }

    private static class AttributeNameRangeFinder extends VoidVisitorAdapter<Object> {
        private final String attributeName;
        private final int lineNumber;
        private String attributeNameRange;

        public AttributeNameRangeFinder(String attributeName, int lineNumber) {
            this.attributeName = attributeName;
            this.lineNumber = lineNumber;
        }

        public String getAttributeNameRange() {
            return attributeNameRange;
        }

        @Override
        public void visit(FieldDeclaration fd, Object arg) {
            super.visit(fd, arg);
            for (VariableDeclarator vd : fd.getVariables()) {
                System.out.println(vd.getNameAsString());
                System.out.println(attributeName);
                if (vd.getNameAsString().equals(attributeName)) {
                    Optional<com.github.javaparser.Range> range = vd.getName().getRange();
                    if (range.isPresent() && range.get().begin.line == lineNumber) {
                        attributeNameRange = range.get().begin.line + ", " +
                                             range.get().begin.column + ", " +
                                             range.get().end.line + ", " +
                                             range.get().end.column;
                    }
                }
            }
        }
    }
}
