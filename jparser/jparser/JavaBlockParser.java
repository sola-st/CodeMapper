package jparser;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.stmt.*;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;

public class JavaBlockParser {
    /*
     * Blocks can be the following types: (refer to codetracker readme)
        1. FOR_STATEMENT
        2. ENHANCED_FOR_STATEMENT
        3. WHILE_STATEMENT
        4. IF_STATEMENT
        5. DO_STATEMENT
        6. SWITCH_STATEMENT
        7. SYNCHRONIZED_STATEMENT
        8. TRY_STATEMENT
        9. CATCH_CLAUSE
        10. FINALLY_BLOCK
     */

    public static List<String> parseJavaFileForBlocks(String filePath, String blockType, int startLine, int endLine) {
        List<String> blockRanges = new ArrayList<>();
        try {
            CompilationUnit cu = StaticJavaParser.parse(new File(filePath));

            // Create a visitor that dynamically checks the type of block
            new VoidVisitorAdapter<Object>() {
                @Override
                public void visit(ForStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("for") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }
                // TODO: check what is enhanced for
                // @Override
                // public void visit( stmt, Object arg) {
                //     if (blockType.equalsIgnoreCase("for") && isWithinRange(stmt, startLine, endLine)) {
                //         addBlockRange(stmt, blockRanges);
                //     }
                //     super.visit(stmt, arg);
                // }

                @Override
                public void visit(WhileStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("while") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }

                @Override
                public void visit(IfStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("if") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }
                // TODO: check how to get "half" if blocks
                // @Override
                // public void visit(IfStmt stmt, Object arg) {
                //     // Add the range for the if block
                //     addBlockRange(stmt, blockRanges);
                    
                //     // Check if there is an else statement and handle it
                //     if (stmt.getElseStmt().isPresent()) {
                //         // Recursively visit the else statement
                //         stmt.getElseStmt().get().accept(this, arg);
                //     }
                //     super.visit(stmt, arg);
                // }

                @Override
                public void visit(DoStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("do") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }

                @Override
                public void visit(SwitchStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("switch") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }

                @Override
                public void visit(TryStmt stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("try") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    } else { // final clause
                        if (stmt.getFinallyBlock().isPresent()) {
                            BlockStmt finallyBlock = stmt.getFinallyBlock().get();
                            addBlockRange(finallyBlock, blockRanges);
                        }
                    }
                    super.visit(stmt, arg);
                }

                @Override
                public void visit(CatchClause stmt, Object arg) {
                    if (blockType.equalsIgnoreCase("catch") && isWithinRange(stmt, startLine, endLine)) {
                        addBlockRange(stmt, blockRanges);
                    }
                    super.visit(stmt, arg);
                }

            }.visit(cu, null);

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return blockRanges;
    }

    private static void addBlockRange(Node node, List<String> blockRanges) {
        String range = node.getBegin().get().line + ", " +
                       node.getBegin().get().column + ", " +
                       node.getEnd().get().line + ", " +
                       node.getEnd().get().column;
        blockRanges.add("[" + range + "]");
    }

    private static boolean isWithinRange(Node node, int startLine, int endLine) {
        int nodeStartLine = node.getBegin().get().line;
        int nodeEndLine = node.getEnd().get().line;
        return nodeStartLine >= startLine && nodeEndLine <= endLine;
    }
}
