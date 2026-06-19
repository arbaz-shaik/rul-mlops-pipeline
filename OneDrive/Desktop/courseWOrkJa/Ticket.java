// Ticket.java
// Represents a show ticket

public class Ticket implements Comparable<Ticket> {
    private int id;
    private String name;
    private int available;
    private double price;

    public Ticket(int id, String name, int available, double price) {
        this.id = id;
        this.name = name;
        this.available = available;
        this.price = price;
    }

    public int getId() { return id; }
    public String getName() { return name; }
    public int getAvailable() { return available; }
    public double getPrice() { return price; }

    public void setAvailable(int available) { this.available = available; }

    @Override
    public int compareTo(Ticket other) {
        return this.name.compareToIgnoreCase(other.name);
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof Ticket)) return false;
        return ((Ticket) obj).name.equalsIgnoreCase(this.name);
    }

    @Override
    public String toString() {
        return String.format("%-35s | Available: %-3d | Price: £%.2f", name, available, price);
    }
}
