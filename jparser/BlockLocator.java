/* 
Supported blockType examples:
    1 IfStmt
    2 ForStmt
    3 WhileStmt
    4 DoStmt
    5 SwitchStmt
    6 BlockStmt
    7 TryStmt
    8 SynchronizedStmt

2
CodeElementType.FOR_STATEMENT
CodeElementType.ENHANCED_FOR_STATEMENT

3
CodeElementType.WHILE_STATEMENT

1
CodeElementType.IF_STATEMENT

4
CodeElementType.DO_STATEMENT

5
CodeElementType.SWITCH_STATEMENT

8
CodeElementType.SYNCHRONIZED_STATEMENT

7
CodeElementType.TRY_STATEMENT

CodeElementType.CATCH_CLAUSE

CodeElementType.FINALLY_BLOCK

*/


import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.stmt.ForStmt;
import com.github.javaparser.ast.stmt.ForEachStmt;
import com.github.javaparser.ast.stmt.WhileStmt;
import com.github.javaparser.ast.stmt.DoStmt;
import com.github.javaparser.ast.stmt.IfStmt;
import com.github.javaparser.ast.stmt.SwitchStmt;
import com.github.javaparser.ast.stmt.SynchronizedStmt;
import com.github.javaparser.ast.stmt.TryStmt;
import com.github.javaparser.ast.stmt.CatchClause;
import com.github.javaparser.ast.stmt.BlockStmt;


public class BlockLocator {

    public static void locateBlock(String filePath, String codeElementType, int targetStartLine, int targetEndLine) {
        File file = new File(filePath);
        if (!file.exists()) {
            System.err.println("File not found: " + filePath);
            return;
        }
        
        // CompilationUnit cu = StaticJavaParser.parse(file);
        CompilationUnit cu;
        try (FileInputStream fis = new FileInputStream(file);
            InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8)) {
            cu = StaticJavaParser.parse(isr);
        } catch (Exception e) {
            System.err.println("Error parsing file: " + e.getMessage());
            return;
        }

        cu.walk(node -> {
            if (!node.getRange().isPresent()) return;

            int start = node.getRange().get().begin.line;
            int end = node.getRange().get().end.line;

            if (start == targetStartLine && end == targetEndLine) {
                boolean match = false;

                switch (codeElementType) {
                    case "FOR_STATEMENT":
                        match = node instanceof ForStmt || node instanceof ForEachStmt;
                        break;
                    case "ENHANCED_FOR_STATEMENT":
                        match = node instanceof ForEachStmt;
                        break;
                    case "WHILE_STATEMENT":
                        match = node instanceof WhileStmt;
                        break;
                    case "IF_STATEMENT":
                        match = node instanceof IfStmt;
                        break;
                    case "DO_STATEMENT":
                        match = node instanceof DoStmt;
                        break;
                    case "SWITCH_STATEMENT":
                        match = node instanceof SwitchStmt;
                        break;
                    case "SYNCHRONIZED_STATEMENT":
                        match = node instanceof SynchronizedStmt;
                        break;
                    case "TRY_STATEMENT":
                        match = node instanceof TryStmt;
                        break;
                    case "CATCH_CLAUSE":
                        match = node instanceof CatchClause;
                        break;
                    case "FINALLY_BLOCK":
                        if (node instanceof BlockStmt && node.getParentNode().isPresent()) {
                            Node parent = node.getParentNode().get();
                            if (parent instanceof TryStmt) {
                                TryStmt tryStmt = (TryStmt) parent;
                                match = tryStmt.getFinallyBlock().isPresent()
                                        && tryStmt.getFinallyBlock().get() == node;
                            }
                        }
                        break;
                }

                if (match) {
                    node.getRange().ifPresent(range -> {
                        System.out.println("[" + range.begin.line + ", " + range.begin.column + ", " +
                                range.end.line + ", " + range.end.column + "]");
                    });
                }
            }
        });
    }

    public static void main(String[] args) {
        if (args.length < 4) {
            System.err.println("Usage: java BlockLocator <filePath> <BlockType> <StartLine> <EndLine>");
            System.exit(1);
        }

        String filePath = args[0];
        String codeElementType = args[1];
        int startLine = Integer.parseInt(args[2]);
        int endLine = Integer.parseInt(args[3]);

        locateBlock(filePath, codeElementType, startLine, endLine);
    }
}
