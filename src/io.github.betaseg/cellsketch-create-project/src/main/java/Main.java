import de.frauzufall.cellsketch.command.CellSketchCreator;
import loci.common.DebugTools;

import java.util.regex.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;

public class Main {
	public static void main(String...args) throws ExecutionException, InterruptedException {
		DebugTools.setRootLevel("INFO");
		List<String> matchList = new ArrayList<String>();
        Pattern regex = Pattern.compile("[^\\s\"']+|\"([^\"]*)\"|'([^']*)'");
        Matcher regexMatcher = regex.matcher(args[0]);
        while (regexMatcher.find()) {
            if (regexMatcher.group(1) != null) {
                // Add double-quoted string without the quotes
                matchList.add(regexMatcher.group(1));
            } else if (regexMatcher.group(2) != null) {
                // Add single-quoted string without the quotes
                matchList.add(regexMatcher.group(2));
            } else {
                // Add unquoted word
                matchList.add(regexMatcher.group());
            }
        }
		CellSketchCreator.main(matchList.toArray(new String[0]));
	}
}
