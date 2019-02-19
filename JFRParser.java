package com.roysunnysean007.performance.gcutil;


import static com.oracle.jmc.common.item.Attribute.attr;
import static com.oracle.jmc.common.unit.UnitLookup.BYTES;
import static com.oracle.jmc.common.unit.UnitLookup.MEMORY;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Properties;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import com.oracle.jmc.common.IMCFrame;
import com.oracle.jmc.common.item.IAttribute;
import com.oracle.jmc.common.item.IItem;
import com.oracle.jmc.common.item.IItemCollection;
import com.oracle.jmc.common.item.IItemFilter;
import com.oracle.jmc.common.item.IItemIterable;
import com.oracle.jmc.common.item.ItemFilters;
import com.oracle.jmc.common.unit.IQuantity;
import com.oracle.jmc.common.unit.ITypedQuantity;
import com.oracle.jmc.common.unit.LinearUnit;
import com.oracle.jmc.common.util.MCStackTrace;
import com.oracle.jmc.flightrecorder.CouldNotLoadRecordingException;
import com.oracle.jmc.flightrecorder.JfrLoaderToolkit;
import com.oracle.jmc.flightrecorder.jdk.JdkTypeIDs;

public class JFRParser {
	static final Logger logger = LogManager.getLogger("humongousObject_log");
	static final Logger parserlogger = LogManager.getLogger("jfrparser_log");
	private static Properties p = new Properties();

	public static void main(String[] args) {
		FileInputStream propFile = null;
		try {
			propFile = new FileInputStream("./conf/runtime.properties");
			p.load(propFile);

		} catch (FileNotFoundException e) {
			parserlogger.error("Can not find ./conf/runtime.properties");
			return;
		} catch (IOException e) {
			parserlogger.error("Fail to load ./conf/runtime.properties");
			return;
		}

		long timestamp1 = System.currentTimeMillis();

		File file = new File(p.getProperty("jfrfileorfolder").trim());
		if (!file.exists()) {
			parserlogger.error("File or Path " + args[0] + " do not exist!");
			return;
		}
		if (file.isFile()) {

			if (!args[0].endsWith(".jfr")) {
				parserlogger.error("Usage: java -jar JFRParser.jar <JFR file>/<JFR file folder>");
				parserlogger.error("JFR file name " + args[0] + " is not ended with .jfr");
				return;
			} else {
				parserlogger.info("**************************************************");
				parserlogger.info("[" + file.getName() + "]Begin to parse JFR file");
				parseJFR(file);
				parserlogger.info("[" + file.getName() + "]Finish parse JFR file");

			}
		} else if (file.isDirectory()) {

			File[] fileList = file.listFiles(new MyFilter());
			for (File afile : fileList) {
				parserlogger.info("**************************************************");
				parserlogger.info("[" + afile.getName() + "]Begin to parse JFR file");
				parseJFR(afile);
				parserlogger.info("[" + afile.getName() + "]Finish parse JFR file");

			}

		} else {
			parserlogger.error(args[0] + " is not a file or directory!");
		}

		long timestamp2 = System.currentTimeMillis();

		long diff = timestamp2 - timestamp1;
		parserlogger.info("Totally it took " + diff / 1000 + " seconds to parse all JFR files ");

	}

	private static void parseJFR(File JFRFile) {
		String jfrfile = JFRFile.getName();
		String allocation_Size_inMB = "";
		String allocation_Size_inB = "";
		StringBuilder stacktrace = new StringBuilder();
		String topClass = "";
		String allocation_endtime = "";
		String threadname = "";
		IItemCollection events;
		try {
			events = JfrLoaderToolkit.loadEvents(JFRFile);
			IItemCollection a = events.apply(ItemFilters.type(JdkTypeIDs.ALLOC_OUTSIDE_TLAB));
			LinearUnit B = BYTES;
			IAttribute<IQuantity> HIGHFIELD_ATTRIBUTE = attr("allocationSize", "Allocation Size", MEMORY);
			int thresholdInMB = Integer.parseInt(p.getProperty("thresholdInMB_humongousObject").trim());

			IItemFilter moreFilter = ItemFilters.more(HIGHFIELD_ATTRIBUTE, B.quantity(thresholdInMB * 1024 * 1024));
			IItemCollection b = a.apply(moreFilter);

			for (IItemIterable ii : b) {

				parserlogger.info("[" + JFRFile.getName() + "]# of humongous objects: " + ii.getItemCount());
				Iterator<IItem> it = ii.iterator();
				List<IAttribute<?>> attilist = ii.getType().getAttributes();
				while (it.hasNext()) {
					stacktrace.setLength(0);
					allocation_Size_inMB = "";
					allocation_Size_inB = "";
					topClass = "";
					allocation_endtime = "";
					threadname = "";
					IItem iitema = it.next();
					for (int dd = 0; dd < attilist.size(); dd++) {

						IAttribute iiatribute;

						if (attilist.get(dd).getName().equals("Allocation Size")) {

							String sstring = attilist.get(dd).getAccessor(ii.getType()).getMember(iitema).toString();
							int charB = sstring.indexOf('B');
							long allocationSize = Long.parseLong(sstring.substring(0, charB));

							DecimalFormat df = new DecimalFormat("#.##");
							// Assumption: Based on 36G heap size, humongous object is 8M given 16M default
							// region size in G1. Set unit of allocation size to MB.
							// If humongous object is in KB level, we had better downgrade unit of
							// allocation size to KB.
							allocation_Size_inMB = df.format(allocationSize / 1024 / 1024.0);
							allocation_Size_inB = allocationSize + "";

							for (int dd2 = 0; dd2 < attilist.size(); dd2++) {

								if (attilist.get(dd2).getName().equals("Stack Trace")) {

									iiatribute = attilist.get(dd2);

									MCStackTrace astackt = (MCStackTrace) iiatribute.getAccessor(ii.getType())
											.getMember(iitema);
									List<IMCFrame> ilist = astackt.getFrames();

									for (int i = 0; i < ilist.size(); i++) {

										stacktrace.append(ilist.get(i).getMethod().getType().getFullName() + ".");
										stacktrace.append(ilist.get(i).getMethod().getMethodName());
										stacktrace.append("(" + ilist.get(i).getMethod().getType().getTypeName()
												+ ".java:" + ilist.get(i).getFrameLineNumber() + ")\n");

									}

								}
							}
							for (int dd3 = 0; dd3 < attilist.size(); dd3++) {

								if (attilist.get(dd3).getName().equals("End Time")) {

									iiatribute = attilist.get(dd3);
									SimpleDateFormat simpleDateFormat = new SimpleDateFormat("MM/dd/yyyy' 'HH:mm:ss:S");
									ITypedQuantity iquantity = (ITypedQuantity) iiatribute.getAccessor(ii.getType())
											.getMember(iitema);

									String input = iquantity.displayUsing(iquantity.EXACT);
									DateTimeFormatter oldPattern = DateTimeFormatter.ofPattern("M/d/y',' h:m:s.n a");
									DateTimeFormatter newPattern = DateTimeFormatter
											.ofPattern("yyyy-MM-dd'T'HH:mm:ss.n");
									LocalDateTime datetime = LocalDateTime.parse(input, oldPattern);
									String output = datetime.format(newPattern);

									allocation_endtime = output;

								}
							}

							for (int dd3 = 0; dd3 < attilist.size(); dd3++) {

								if (attilist.get(dd3).getName().equals("Thread")) {

									iiatribute = attilist.get(dd3);
									threadname = iiatribute.getAccessor(ii.getType()).getMember(iitema).toString();

								}
							}

							for (int dd4 = 0; dd4 < attilist.size(); dd4++) {

								if (attilist.get(dd4).getName().equals("Class")) {

									iiatribute = attilist.get(dd4);
									topClass = iiatribute.getAccessor(ii.getType()).getMember(iitema).toString();

								}
							}

						}
					}
					// Sample of jfrstring is humongousObject_DC13BIZX5CFAPP03_20180830_010214.jfr
					logger.info(allocation_endtime + "  " + "SizeInMB=" + allocation_Size_inMB + " SizeInB="
							+ allocation_Size_inB + " Class=" + topClass + " Thread=" + threadname + " EndTime="
							+ allocation_endtime + " Jfrfile=" + jfrfile + " Host=" + jfrfile
									.substring(jfrfile.indexOf("_") + 1, jfrfile.indexOf("_", jfrfile.indexOf("_") + 1))
							+ " Stacktrace=" + stacktrace);
				}
			}
		} catch (IOException e) {
			parserlogger.error("[" + JFRFile.getName() + "]IOException JFR file " + jfrfile);

		} catch (CouldNotLoadRecordingException e) {
			parserlogger.error("[" + JFRFile.getName() + "]Could not JFR file " + jfrfile);

		} catch (NumberFormatException e) {
			parserlogger.error("Threshold for humongousObject " + p.getProperty("thresholdInMB_humongousObject").trim()
					+ "is NOT number!");
			return;
		}

	}

}
