import com.github.javaparser.ParseProblemException;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.AnnotationDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class parser {

    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: java -jar <jar_file> <path_to_java_file>");
            System.exit(1);
        }

        File javaFile = new File(args[0]);
        if (!javaFile.exists()) {
            System.err.println("Error: File not found at " + args[0]);
            System.exit(1);
        }

        try {
            String sourceCode = new String(Files.readAllBytes(javaFile.toPath()), StandardCharsets.UTF_8);
            CompilationUnit cu = StaticJavaParser.parse(sourceCode);

            List<Map<String, Object>> entries = new ArrayList<>();
            String filePath = javaFile.getAbsolutePath();

            // Package
            cu.getPackageDeclaration().ifPresent(p -> entries.add(createEntry("package", p.getNameAsString(), p, filePath)));

            // Imports
            cu.getImports().forEach(i -> entries.add(createEntry("import", i.getNameAsString(), i, filePath)));

            // Types (Class, Interface, Enum, etc.)
            cu.getTypes().forEach(type -> {
                if (type instanceof ClassOrInterfaceDeclaration) {
                    ClassOrInterfaceDeclaration cid = (ClassOrInterfaceDeclaration) type;
                    entries.add(createEntry(cid.isInterface() ? "interface" : "class", cid.getNameAsString(), cid, filePath));
                } else if (type instanceof EnumDeclaration) {
                    entries.add(createEntry("enum", type.getNameAsString(), type, filePath));
                } else if (type instanceof AnnotationDeclaration) {
                    entries.add(createEntry("annotation", type.getNameAsString(), type, filePath));
                }

                // Fields
                type.getFields().forEach(field -> {
                    field.getVariables().forEach(variable -> {
                        entries.add(createEntry("field", variable.getNameAsString(), field, filePath));
                    });
                });

                // Constructors
                type.getConstructors().forEach(constructor -> {
                    entries.add(createEntry("constructor", constructor.getNameAsString(), constructor, filePath));
                });

                // Methods
                type.getMethods().forEach(method -> {
                    entries.add(createEntry("method", method.getNameAsString(), method, filePath));
                });
            });

            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            System.out.println(gson.toJson(entries));

        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
            System.exit(1);
        } catch (ParseProblemException e) {
            System.err.println("Error parsing file " + args[0] + ": " + e.getMessage());
             // 파싱 에러가 나도 빈 결과를 반환하여 다음 파일 처리를 계속하도록 함
            System.out.println("[]");
        }
    }

    private static Map<String, Object> createEntry(String type, String name, Node node, String filePath) {
        Map<String, Object> entry = new LinkedHashMap<>();
        entry.put("type", type);
        entry.put("name", name);
        // getRange is optional, so we handle its absence
        node.getRange().ifPresent(r -> {
            entry.put("start_line", r.begin.line);
            entry.put("end_line", r.end.line);
        });
        // toString() provides the raw code of the node
        entry.put("code", node.toString());
        entry.put("file_path", filePath);
        return entry;
    }
}