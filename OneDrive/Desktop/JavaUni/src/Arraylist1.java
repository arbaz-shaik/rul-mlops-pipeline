import java.util.ArrayList;
import java.util.Arrays;

public class Arraylist1 {

    private  String[] array;
    Arraylist1(String[] array){
        this.array = array;
    }
    public String[] getArray(){
        return array;
    }
    public void setArray(String[] array){
        this.array = array;
    }

    @Override
    public String toString() {
        return "Arraylist1{" + "array=" + Arrays.toString(array) + '}';
    }

}
