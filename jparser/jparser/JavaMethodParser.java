package jparser;


import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;


public class JavaMethodParser {
    public static String[] getParameterTypeList(String parameterTypesString){
        String[] paraTypes = {};
        if(parameterTypesString != "") {
            paraTypes = parameterTypesString.split(",");
        }
        
        return paraTypes;
    }
    
    public static List<String> parseJavaFile(String filePath, String methodName, String parameterTypes) {
        List<String> methodRange = new ArrayList<>();
        boolean[] foundMethod = {false};
        
        String[] targetParaTypes = getParameterTypeList(parameterTypes);

        try {
            CompilationUnit cu = StaticJavaParser.parse(new File(filePath));

            new VoidVisitorAdapter<Object>() {
                @Override
                public void visit(MethodDeclaration md, Object arg) {
                    super.visit(md, arg);
                    if (!foundMethod[0] && md.getNameAsString().equals(methodName)) {
                        NodeList<Parameter> parsedParaTypes = md.getParameters(); // String.valueOf
                        if (parsedParaTypes != null) {
                            int paraNum = targetParaTypes.length;
                            int containsNum = 0;
                            if (paraNum == parsedParaTypes.size()) {
                                for (int i=0; i<paraNum; i++){
                                    if (String.valueOf(parsedParaTypes.get(i)).contains(targetParaTypes[i].strip())) {
                                        containsNum+=1;
                                    }
                                }
                            }
                            if (paraNum == containsNum){
                                foundMethod[0] = true;
                            }
                        } else {
                            if (parameterTypes == null){
                                foundMethod[0] = true;
                            }
                        }
                        
                        if (foundMethod[0]){
                            String r = md.getBegin().get().line + ", " +
                                    md.getBegin().get().column + ", " + md.getEnd().get().line
                                    + ", " + md.getEnd().get().column;
                            methodRange.add(r);
                        }
                    }
                }
            }.visit(cu, null);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return methodRange;
    }
}