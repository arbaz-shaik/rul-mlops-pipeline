
from torch import nn

class RULModel(nn.Module):
    '''
    LSTM model for RUL prediction.'''
    def __init__(self, input_size=14, hidden_size_1=64, hidden_size_2=32, dropout=0.2):  
        '''
        Initialize the LSTM model
        LSTM model with 2 layers and dropout for RUL prediction.
        Args:
            input_size (int): Number of input features.
            hidden_size_1 (int): Number of features in the first hidden state.
            hidden_size_2 (int): Number of features in the second hidden state.
            dropout (float): Dropout probability.
        '''
        super(RULModel, self).__init__()
        
        self.lstm1 = nn.LSTM(input_size=input_size, hidden_size=hidden_size_1, num_layers=1, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.lstm2 = nn.LSTM(input_size=hidden_size_1, hidden_size=hidden_size_2, num_layers=1, batch_first=True)
        self.fc = nn.Linear(hidden_size_2, 1)

    def forward(self, x):
        ''''
        Forward pass of the model.
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, sequence_length, input_size).'''
        lstm_out, _ = self.lstm1(x)
        lstm_out = self.dropout(lstm_out)
        lstm_out, _ = self.lstm2(lstm_out)
        lstm_out = self.fc(lstm_out[:, -1, :]) 
        return lstm_out
    
