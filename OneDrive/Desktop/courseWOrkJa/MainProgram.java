// MainProgram.java
// CSC8023 Coursework 2025/26
// Interactive ticket/member system with letters.txt generation

import java.io.*;
import java.util.*;

public class MainProgram {
    private static SortedLinkedList<Ticket> ticketList = new SortedLinkedList<>();
    private static HashMap<String, Ticket> ticketLookup = new HashMap<>();
    private static HashMap<String, Member> members = new HashMap<>();

    public static void main(String[] args) {
        loadData();
        runMenu();
    }

    private static void loadData() {
        try (Scanner sc = new Scanner(new File("input_data.txt"))) {
            int memberCount = Integer.parseInt(sc.nextLine().trim());
            for (int i = 0; i < memberCount; i++) {
                String[] nameParts = sc.nextLine().trim().split(" ", 2);
                members.put(nameParts[0] + " " + nameParts[1],
                            new Member(nameParts[0], nameParts[1]));
            }

            int ticketCount = Integer.parseInt(sc.nextLine().trim());
            for (int i = 0; i < ticketCount; i++) {
                String name = sc.nextLine().trim();
                int qty = Integer.parseInt(sc.nextLine().trim());
                double price = Double.parseDouble(sc.nextLine().trim());
                Ticket t = new Ticket(i + 1, name, qty, price);
                ticketList.insert(t);
                ticketLookup.put(name, t);
            }

            System.out.println("✅ Data loaded successfully.");
        } catch (Exception e) {
            System.out.println("⚠️ Error reading input_data.txt: " + e.getMessage());
        }
    }

    private static void runMenu() {
        Scanner sc = new Scanner(System.in);
        String choice;

        do {
            System.out.println("\n--- MENU ---");
            System.out.println("f - Finish");
            System.out.println("t - Display all tickets");
            System.out.println("m - Display all members");
            System.out.println("b - Buy tickets");
            System.out.println("c - Cancel tickets");
            System.out.print("Enter choice: ");
            choice = sc.nextLine().trim().toLowerCase();

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
        } while (!choice.equals("f"));
    }

    private static void displayTickets() {
        System.out.println("\n--- Ticket Information ---");
        ticketList.display();
    }

    private static void displayMembers() {
        System.out.println("\n--- Member Information ---");
        for (Member m : members.values()) {
            m.display(ticketLookup);
            System.out.println();
        }
    }

    private static void buyTickets(Scanner sc) {
        System.out.print("Enter member name (First Last): ");
        String name = String.join(" ", sc.nextLine().trim().split("\\s+"));
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

        System.out.print("Enter quantity to buy: ");
        int qty = Integer.parseInt(sc.nextLine().trim());

        if (qty > t.getAvailable()) {
            System.out.println("❌ Not enough tickets available. Writing letter...");
            writeLetter(m, t, qty);
            return;
        }

        m.buyTicket(t, qty);
    }

    private static void cancelTickets(Scanner sc) {
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


        System.out.println("Enter quantity to cancel: ");
        int qty = Integer.parseInt(sc.nextLine().trim());
        m.cancelTicket(t, qty);
    }

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
            System.out.println("⚠️ Error writing to letters.txt: " + e.getMessage());
        }
    }
}
