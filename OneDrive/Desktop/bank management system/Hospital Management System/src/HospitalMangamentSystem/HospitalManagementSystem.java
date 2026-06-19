package HospitalMangamentSystem;

import java.sql.*;
import java.util.Scanner;

public class HospitalManagementSystem {
    static Scanner scanner = new Scanner(System.in);

    private static final String url = "jdbc:mysql://localhost:3306/hospital";
    private static final String username = "root";
    private static final String password = "Arbaz@799489";

    public static void main(String[] args) {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");

        } catch (ClassNotFoundException e) {
            e.printStackTrace();

        }

        try {
            Connection connection = DriverManager.getConnection(url, username, password);
            Patient patient = new Patient(connection, scanner);
            Doctors doctors = new Doctors(connection);
            while (true) {
                System.out.println("\n=== HOSPITAL MANAGEMENT SYSTEM ===");
                System.out.println("1. Add Patient");
                System.out.println("2. View Patients");
                System.out.println("3. View Doctors");
                System.out.println("4. Book Appointment");
                System.out.println("5. Exit");
                System.out.print("Enter choice: ");

                int choice = scanner.nextInt();

                switch (choice) {
                    case 1:
                        patient.addPatient();
                        break;

                    case 2:
                        patient.viewPatients();
                        break;

                    case 3:
                        doctors.viewDoctors();
                        break;

                    case 4:
                        bookAppointment(patient, doctors, connection, scanner);
                        break;

                    case 5:
                        System.out.println("Exiting system...");
                        connection.close();
                        scanner.close();
                        System.exit(0);
                        break;

                    default:
                        System.out.println("Invalid choice! Please try again.");
                }
            }


        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static void bookAppointment(Patient patient, Doctors doctors, Connection connection, Scanner scanner) {
        System.out.println("enter patient ID");
        int patientId = scanner.nextInt();
        System.out.println("enter doctor ID");
        int doctorId = scanner.nextInt();
        System.out.println("enter appointment ID (YYYY-MM-DD)");
        String appointment = scanner.next();
        if (patient.patientExistsById(patientId) && doctors.doctorExistsById(doctorId)) {

            if (checkDocAvailable(doctorId, appointment, connection)) {
                String appQuery = "INSERT INTO appointments(pa_id,d_id, appointment) VALUES (?,?)";
                try {
                    PreparedStatement preparedStatement = connection.prepareStatement(appQuery);
                    preparedStatement.setInt(1, patientId);
                    preparedStatement.setInt(2, doctorId);
                    preparedStatement.setString(3, appointment);
                    if (preparedStatement.executeUpdate() == 0) {
                        System.out.println("Appointment not found!");
                    } else {
                        System.out.println("Appointment has been booked!");
                    }
                } catch (SQLException e) {
                    e.printStackTrace();
                }
            } else {
                System.out.println("Sorry Doctor is not available");
            }
        } else {
            System.out.println("Patient or Doctor does not exist!");

        }


    }

    public static boolean checkDocAvailable(int doctorId, String appointment, Connection connection) {
        String query = "SELECT * FROM appointments WHERE d_id=? AND appointment=?";
        try {
            PreparedStatement preparedStatement = connection.prepareStatement(query);
            preparedStatement.setInt(1, doctorId);
            preparedStatement.setString(2, appointment);
            ResultSet resultSet = preparedStatement.executeQuery();
            if (resultSet.next()) {
                int count = resultSet.getInt(1);
                if (count == 0) {
                    return true;
                }
                else  {
                    return false;
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }



        return false;
    }

}






