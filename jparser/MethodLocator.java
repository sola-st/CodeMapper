import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.type.Type;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;

public class MethodLocator {

    public static void locateMethod(String filePath, String methodName, List<String> paramTypeList) {
        File file = new File(filePath);
        if (!file.exists()) {
            System.err.println("File not found: " + filePath);
            return;
        }

        try (FileInputStream fis = new FileInputStream(file);
             InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8)) {

            CompilationUnit cu = StaticJavaParser.parse(isr);

            cu.findAll(MethodDeclaration.class).forEach(method -> {
                if (!method.getNameAsString().equals(methodName)) return;

                List<String> methodParamTypes = method.getParameters().stream()
                        .map(p -> p.getType().asString())
                        .collect(Collectors.toList());

                if (methodParamTypes.equals(paramTypeList)) {
                    method.getRange().ifPresent(range -> {
                        System.out.println("[" + range.begin.line + ", " + range.begin.column + ", " +
                                range.end.line + ", " + range.end.column + "]");
                    });
                }
            });

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        if (args.length < 3) {
            System.err.println("Usage: java MethodLocator <filePath> <methodName> <commaSeparatedParamTypes>");
            System.exit(1);
        }

        String filePath = args[0];
        String methodName = args[1];
        String[] paramTypesArray = args[2].split(",");
        List<String> paramTypeList = List.of(paramTypesArray);

        locateMethod(filePath, methodName, paramTypeList);
    }
}
