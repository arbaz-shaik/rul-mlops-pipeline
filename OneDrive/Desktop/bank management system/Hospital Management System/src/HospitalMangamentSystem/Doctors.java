package HospitalMangamentSystem;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Scanner;

public class Doctors {

    private Connection connection;

    public Doctors(Connection connection) {
        this.connection = connection;
    }

    // VIEW DOCTORS
    public void viewDoctors() {

        try {
            String query = "SELECT * FROM doctors";
            PreparedStatement ps = connection.prepareStatement(query);
            ResultSet rs = ps.executeQuery();

            System.out.println("\n--- Doctors List ---");
            while (rs.next()) {
                System.out.println(
                        "ID: " + rs.getInt("d_id") +
                                ", Name: " + rs.getString("name") +
                                ", Specialization: " + rs.getString("specialization") +
                                ", Join Date: " + rs.getString("app_date")
                );
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    // CHECK DOCTOR EXISTS
    public boolean doctorExistsById(int id) {


            try {
                String query = "SELECT 1 FROM doctors WHERE d_id = ?";
                PreparedStatement ps = connection.prepareStatement(query);
                ps.setInt(1, id);
                ResultSet rs = ps.executeQuery();
                return rs.next();
            } catch (SQLException e) {
                e.printStackTrace();
            }
            return false;
        }

    }

