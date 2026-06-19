// Member.java
// Represents a member who can purchase and cancel tickets

import java.util.*;

public class Member {
    private String firstName;
    private String surname;
    private Map<String, Integer> purchasedTickets = new HashMap<>();

    public Member(String firstName, String surname) {
        this.firstName = firstName;
        this.surname = surname;
    }

    public String getFullName() {
        return firstName + " " + surname;
    }

    public void buyTicket(Ticket t, int qty) {
        String name = t.getName();
        if (!purchasedTickets.containsKey(name) && purchasedTickets.size() >= 3) {
            System.out.println("❌ " + getFullName() + " already holds 3 types of tickets.");
            return;
        }

        int owned = purchasedTickets.getOrDefault(name, 0);
        purchasedTickets.put(name, owned + qty);
        t.setAvailable(t.getAvailable() - qty);
        System.out.println("✅ " + getFullName() + " bought " + qty + " ticket(s) for " + name);
    }

    public void cancelTicket(Ticket t, int qty) {
        String name = t.getName();
        if (!purchasedTickets.containsKey(name)) {
            System.out.println("❌ " + getFullName() + " does not own any " + name + " tickets.");
            return;
        }

        int owned = purchasedTickets.get(name);
        if (qty >= owned) {
            purchasedTickets.remove(name);
        } else {
            purchasedTickets.put(name, owned - qty);
        }

        t.setAvailable(t.getAvailable() + qty);
        System.out.println("↩️ " + getFullName() + " cancelled " + qty + " ticket(s) for " + name);
    }

    public double getTotalCost(Map<String, Ticket> ticketLookup) {
        double total = 0;
        for (Map.Entry<String, Integer> e : purchasedTickets.entrySet()) {
            Ticket t = ticketLookup.get(e.getKey());
            if (t != null)
                total += e.getValue() * t.getPrice();
        }
        return total;
    }

    public void display(Map<String, Ticket> ticketLookup) {
        System.out.println("Member: " + getFullName());
        if (purchasedTickets.isEmpty()) {
            System.out.println("  No tickets purchased.");
            return;
        }

        double totalAll = 0;
        for (Map.Entry<String, Integer> e : purchasedTickets.entrySet()) {
            String ticketName = e.getKey();
            int qty = e.getValue();
            Ticket t = ticketLookup.get(ticketName);
            double subtotal = qty * (t != null ? t.getPrice() : 0);
            totalAll += subtotal;
            System.out.printf("  %-35s | Qty: %-3d | Subtotal: £%.2f%n", ticketName, qty, subtotal);
        }
        System.out.printf("  Total spent: £%.2f%n", totalAll);
    }
}
