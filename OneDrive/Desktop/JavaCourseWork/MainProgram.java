// MainProgram.java
// CSC8023 Coursework 2025/26
// Interactive ticket/member system with letters.txt generation

import java.io.*;// this will import all io class for I/O opertion. (*) this will import everthing from the java.io package
import java.util.*;// importing everthing from util.


public class MainProgram {
    //creating objects
    private static SortedLinkedList<Ticket> ticketList = new SortedLinkedList<>();
    private static Map<String, Ticket> ticketLookup = new HashMap<>();
    private static Map<String, Member> members = new HashMap<>();

    /**
     * @see #main(String[])
     * the main program starts here
     *call loadData() to read input files and set out data
    *call menu() to shoe UI and handle input
     */

    public static void main(String[] args) {
        loadData();//
        menu();
    }

    /**
     * @see #loadData()
     *  loads the data from the file
     */

    private static void loadData() {
        try (Scanner sc = new Scanner(new File("input_data.txt"))) {

            int memberCount = Integer.parseInt(sc.nextLine().trim());
            for (int i = 0; i < memberCount; i++) {
                String[] nameParts = sc.nextLine().trim().split(" ", 2);//splits the String convert into array (nameParts[])
                members.put(nameParts[0] + " " + nameParts[1],
                            new Member(nameParts[0], nameParts[1]));// creates a member object stores it in member
            }

            // does the same like member converting creating Ticket object adding it to list
            int ticketCount = Integer.parseInt(sc.nextLine().trim());
            for (int i = 0; i < ticketCount; i++) {
                String name = sc.nextLine().trim();
                int qty = Integer.parseInt(sc.nextLine().trim());// available tickets
                double price = Double.parseDouble(sc.nextLine().trim());// price of ticket
                Ticket t = new Ticket(i + 1, name, qty, price);// here the i+1 gives teh a number like 1,2...
                ticketList.insert(t);
                ticketLookup.put(name, t);
            }

            System.out.println("✅ Data loaded successfully.");
        } catch (Exception e) {
            System.out.println("⚠️ Error reading input_data.txt: " + e.getMessage());
        }
    }

    /**
     * @see #menu()
     * menu displace menu to user
     */

    private static void menu() {
        Scanner sc = new Scanner(System.in);
        String choice;

        // ruuning the menu till user ends it
        do {
            System.out.println("\n--- MENU ---");
            System.out.println("f - Finish");
            System.out.println("t - Display all tickets");
            System.out.println("m - Display all members");
            System.out.println("b - Buy tickets");
            System.out.println("c - Cancel tickets");
            System.out.print("Enter choice: ");
            choice = sc.nextLine().trim().toLowerCase();

            // to run the code according to user choice of input
            switch (choice) {
                case "f":
                    System.out.println("Exiting program...");
                    break;
                case "t":
                    displayTickets();
                    break;
                case "m":
                    displayMembers();
                    break;
                case "b":
                    buyTickets(sc);
                    break;
                case "c":
                    cancelTickets(sc);
                    break;
                default:
                    System.out.println("Invalid choice. Try again.");
            }
        } while (!choice.equals("f"));// ends if user enter f
    }

    /**
     * @see #displayTickets()
     *  to display the ticket to the user when user enter t
     */

    private static void displayTickets() {
        System.out.println("\n--- Ticket Information ---");
        ticketList.display();
    }

    /**
     * @see #displayMembers()
     * displays the members
     */

    private static void displayMembers() {
        System.out.println("\n--- Member Information ---");
        for (Member m : members.values()) {
            m.display(ticketLookup);
            System.out.println();
        }
    }

    /**
     *@see #buyTickets(Scanner)
     * when user enter b to buy ticket
     */

    private static void buyTickets(Scanner sc) {
        System.out.print("Enter member name (First Last): ");
        //takes the member first and last name
        String name = sc.nextLine().trim();
        Member m = members.get(name);
        if (m == null) {
            System.out.println("❌ No such member.");// if the member doesn't exist
            return;
        }

        // if the member exist
        System.out.print("Enter ticket name: ");
        // takes the ticket name they want to buy
        String tname = sc.nextLine().trim();
        Ticket t = ticketLookup.get(tname);
        if (t == null) {
            System.out.println("❌ No such ticket.");// if doesn't exist
            return;
        }

        // takes the number of tickets user wants to buy
        System.out.print("Enter quantity to buy: ");
        int qty = Integer.parseInt(sc.nextLine().trim());

        if (qty > t.getAvailable()) {
            System.out.println("❌ Not enough tickets available. Writing letter...");
            writeLetter(m, t, qty);// if the tickets are not enough writes a letter to user
            return;
        }

        m.buyTicket(t, qty);// calls the member to buy ticket
    }

    /**
     * @see #cancelTickets(Scanner)
     *  when user select c for cancelling
     * @param sc will takes user input
     */

    private static void cancelTickets(Scanner sc) {
        //checks the member if it's null itll print the statement
        System.out.print("Enter member name (First Last): ");
        String name = sc.nextLine().trim();
        Member m = members.get(name);
        if (m == null) {
            System.out.println("❌ No such member.");
            return;
        }

        System.out.print("Enter ticket name: ");
        String tname = sc.nextLine().trim();
        Ticket t = ticketLookup.get(tname);
        if (t == null) {
            System.out.println("❌ No such ticket.");
            return;
        }

        // takes the quatity and calls the member to cancel ticket
        System.out.print("Enter quantity to cancel: ");
        int qty = Integer.parseInt(sc.nextLine().trim());

        m.cancelTicket(t, qty);
    }

    /**
     * @see #writeLetter(Member, Ticket, int) 
    *write a rekection letter when member request
     * @param m member who attemoted booking
     * @param t  tickects requested
     * @param  qty number tickets
     */

    private static void writeLetter(Member m, Ticket t, int qty) {
        try (FileWriter fw = new FileWriter("letters.txt", true);
             PrintWriter pw = new PrintWriter(fw)) {
            pw.println("--------------------------------------------------");
            pw.println("Dear " + m.getFullName() + ",");
            pw.println();
            pw.println("We regret to inform you that your request for " + qty +
                       " ticket(s) to '" + t.getName() + "' could not be fulfilled,");
            pw.println("as there are not enough tickets currently available.");
            pw.println();
            pw.println("Please try again later or choose another event.");
            pw.println();
            pw.println("Kind regards,");
            pw.println("Ticket Office");
            pw.println("--------------------------------------------------\n");
        } catch (IOException e) {
            // error in writing files
            System.out.println("⚠️ Error writing to letters.txt: " + e.getMessage());
        }
    }
}
