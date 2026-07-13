// Ghidra headless script: export a first-pass C decompilation and symbol notes.
// Usage:
//   analyzeHeadless <project_dir> <project_name> -import E2WIN95.EXE \
//     -scriptPath reverse/ghidra_scripts -postScript ExportDecomp.java <out_dir>

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.Iterator;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.util.task.ConsoleTaskMonitor;

public class ExportDecomp extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("Expected output directory argument");
        }

        File outDir = new File(args[0]);
        File srcDir = new File(outDir, "src");
        File metaDir = new File(outDir, "metadata");
        srcDir.mkdirs();
        metaDir.mkdirs();

        DecompileOptions options = new DecompileOptions();
        DecompInterface ifc = new DecompInterface();
        ifc.setOptions(options);
        if (!ifc.openProgram(currentProgram)) {
            throw new RuntimeException("Could not open program in decompiler");
        }

        int ok = 0;
        int failed = 0;
        try (BufferedWriter c = new BufferedWriter(new FileWriter(new File(srcDir, "E2Recomp_decompiled.c")));
             BufferedWriter index = new BufferedWriter(new FileWriter(new File(metaDir, "functions.tsv")))) {
            c.write("/*\n");
            c.write(" * First-pass Ghidra decompilation of " + currentProgram.getExecutablePath() + ".\n");
            c.write(" * This is reconstruction input, not original source.\n");
            c.write(" */\n\n");
            c.write("#include \"e2recomp_types.h\"\n\n");
            index.write("address\tname\tbody_size\tstatus\n");

            Iterator<Function> funcs = currentProgram.getFunctionManager().getFunctions(true);
            while (funcs.hasNext() && !monitor.isCancelled()) {
                Function f = funcs.next();
                DecompileResults res = ifc.decompileFunction(f, 60, new ConsoleTaskMonitor());
                if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
                    String body = res.getDecompiledFunction().getC();
                    c.write("/* ");
                    c.write(f.getEntryPoint().toString());
                    c.write(" */\n");
                    c.write(body);
                    c.write("\n\n");
                    index.write(f.getEntryPoint().toString());
                    index.write("\t");
                    index.write(f.getName());
                    index.write("\t");
                    index.write(Integer.toString(body.length()));
                    index.write("\tok\n");
                    ok++;
                } else {
                    c.write("/* ");
                    c.write(f.getEntryPoint().toString());
                    c.write(" ");
                    c.write(f.getName());
                    c.write(" failed to decompile. */\n\n");
                    index.write(f.getEntryPoint().toString());
                    index.write("\t");
                    index.write(f.getName());
                    index.write("\t0\tfailed\n");
                    failed++;
                }
            }
        } finally {
            ifc.dispose();
        }

        try (BufferedWriter program = new BufferedWriter(new FileWriter(new File(metaDir, "program.tsv")))) {
            program.write("property\tvalue\n");
            program.write("name\t" + currentProgram.getName() + "\n");
            program.write("executable_path\t" + currentProgram.getExecutablePath() + "\n");
            program.write("language\t" + currentProgram.getLanguageID().getIdAsString() + "\n");
            program.write("compiler\t" + currentProgram.getCompilerSpec().getCompilerSpecID().getIdAsString() + "\n");
            program.write("image_base\t" + currentProgram.getImageBase().toString() + "\n");
            program.write("min_address\t" + currentProgram.getMinAddress().toString() + "\n");
            program.write("max_address\t" + currentProgram.getMaxAddress().toString() + "\n");
        }

        try (BufferedWriter symbols = new BufferedWriter(new FileWriter(new File(metaDir, "symbols.tsv")))) {
            symbols.write("address\ttype\tname\n");
            SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Symbol s = it.next();
                symbols.write(s.getAddress().toString());
                symbols.write("\t");
                symbols.write(s.getSymbolType().toString());
                symbols.write("\t");
                symbols.write(s.getName(true));
                symbols.write("\n");
            }
        }

        try (BufferedWriter refs = new BufferedWriter(new FileWriter(new File(metaDir, "references.tsv")))) {
            refs.write("from\tto\ttype\n");
            ReferenceIterator it = currentProgram.getReferenceManager().getReferenceIterator(currentProgram.getMinAddress());
            while (it.hasNext() && !monitor.isCancelled()) {
                Reference r = it.next();
                refs.write(r.getFromAddress().toString());
                refs.write("\t");
                refs.write(r.getToAddress().toString());
                refs.write("\t");
                refs.write(r.getReferenceType().toString());
                refs.write("\n");
            }
        }

        println("Exported " + ok + " functions; failed " + failed + ".");
    }
}
