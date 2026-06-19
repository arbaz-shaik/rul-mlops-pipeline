package HospitalMangamentSystem;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Scanner;

public class Patient {

    private Connection connection;
    private Scanner scanner;

    public Patient(Connection connection, Scanner scanner) {
        this.connection = connection;
        this.scanner = scanner;
    }

    // ADD PATIENT
    public boolean addPatient() {

        System.out.print("Enter Patient Name: ");
        String name = scanner.nextLine();

        System.out.print("Enter Patient Age: ");
        int age = scanner.nextInt();
        scanner.nextLine(); // consume newline

        System.out.print("Enter Patient Gender: ");
        String gender = scanner.nextLine();

        try {
            String query = "INSERT INTO patients (name, age, gender) VALUES (?, ?, ?)";
            PreparedStatement preparedStatement = connection.prepareStatement(query);

            preparedStatement.setString(1, name);
            preparedStatement.setInt(2, age);
            preparedStatement.setString(3, gender);

            int affectedRows = preparedStatement.executeUpdate();

            return affectedRows > 0;

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }

    // VIEW ALL PATIENTS
    public void viewPatients() {

        try {
            String query = "SELECT * FROM patients";
            PreparedStatement preparedStatement = connection.prepareStatement(query);
            ResultSet resultSet = preparedStatement.executeQuery();

            System.out.println("\n--- Patients List ---");
            while (resultSet.next()) {
                System.out.println(
                        "ID: " + resultSet.getInt("p_id") +
                                ", Name: " + resultSet.getString("name") +
                                ", Age: " + resultSet.getInt("age") +
                                ", Gender: " + resultSet.getString("gender")
                );
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    // CHECK IF PATIENT EXISTS BY ID
    public boolean patientExistsById(int id) {

        try {
            String query = "SELECT 1 FROM patients WHERE p_id = ?";
            PreparedStatement preparedStatement = connection.prepareStatement(query);
            preparedStatement.setInt(1, id);

            ResultSet resultSet = preparedStatement.executeQuery();
            return resultSet.next();

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }
}
