import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.VariableDeclarator;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.Parameter;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import java.io.File;

public class VariableDeclarationLocator {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: java VariableDeclarationLocator <JavaFilePath> <TargetLineNumber> <NameToSearch>");
            return;
        }

        String filePath = args[0];
        int targetLine;
        String targetName = args[2];

        try {
            targetLine = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.err.println("Invalid line number: " + args[1]);
            return;
        }

        File file = new File(filePath);
        if (!file.exists()) {
            System.err.println("File not found: " + filePath);
            return;
        }

        CompilationUnit cu = StaticJavaParser.parse(file);

        cu.accept(new VoidVisitorAdapter<Void>() {
            void printIfMatch(String kind, String name, int line, int colStart, int colEnd) {
                if (line == targetLine && name.equals(targetName)) { //kind, e,g, Parameter
                    System.out.println("[" + line + ", " + colStart + ", " + line + ", " + colEnd + "]");
                }
            }

            @Override
            public void visit(VariableDeclarator var, Void arg) {
                var.getName().getRange().ifPresent(range ->
                        printIfMatch("Variable", var.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(var, arg);
            }

            @Override
            public void visit(MethodDeclaration method, Void arg) {
                method.getName().getRange().ifPresent(range ->
                        printIfMatch("Method", method.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(method, arg);
            }

            @Override
            public void visit(ConstructorDeclaration ctor, Void arg) {
                ctor.getName().getRange().ifPresent(range ->
                        printIfMatch("Constructor", ctor.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(ctor, arg);
            }

            @Override
            public void visit(ClassOrInterfaceDeclaration decl, Void arg) {
                decl.getName().getRange().ifPresent(range ->
                        printIfMatch(decl.isInterface() ? "Interface" : "Class", decl.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(decl, arg);
            }

            @Override
            public void visit(EnumDeclaration enumDecl, Void arg) {
                enumDecl.getName().getRange().ifPresent(range ->
                        printIfMatch("Enum", enumDecl.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(enumDecl, arg);
            }

            @Override
            public void visit(FieldDeclaration field, Void arg) {
                field.getVariables().forEach(var ->
                    var.getName().getRange().ifPresent(range ->
                        printIfMatch("Field", var.getNameAsString(), range.begin.line, range.begin.column, range.end.column))
                );
                super.visit(field, arg);
            }

            @Override
            public void visit(Parameter param, Void arg) {
                param.getName().getRange().ifPresent(range ->
                        printIfMatch("Parameter", param.getNameAsString(), range.begin.line, range.begin.column, range.end.column));
                super.visit(param, arg);
            }
        }, null);
    }
}
