package jparser;


import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;


public class JavaClassParser {
    public static List<String> parseJavaFile(String filePath, String className, String accessor) { // , Integer referLine
        List<String> classRange = new ArrayList<>();
        boolean[] foundClass = {false};
        try {
            CompilationUnit cu = StaticJavaParser.parse(new File(filePath));

            new VoidVisitorAdapter<Object>() {
                @Override
                public void visit(ClassOrInterfaceDeclaration cd, Object arg) {
                    super.visit(cd, arg);
                    if (!foundClass[0] && cd.getNameAsString().equals(className)) {
                        String accessSpecifier = String.valueOf(cd.getAccessSpecifier());
                        if (accessor != null){
                            if (accessSpecifier.contains(accessor.toUpperCase())) {
                                foundClass[0] = true;
                            } 
                        } else {
                            if (accessSpecifier == null) {
                                foundClass[0] = true;
                            }
                        }
                        if (foundClass[0]){
                            String r = cd.getBegin().get().line + ", " +
                                        cd.getBegin().get().column + ", " + cd.getEnd().get().line
                                        + ", " + cd.getEnd().get().column;
                            classRange.add(r);
                        }
                    }
                }
            }.visit(cu, null);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return classRange;
    }
}